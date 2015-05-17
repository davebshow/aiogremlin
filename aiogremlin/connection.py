"""
"""
import asyncio
import base64
import hashlib
import os

from aiohttp import (client, hdrs, DataQueue, StreamParser,
    WSServerHandshakeError)
from aiohttp.errors import WSServerHandshakeError
from aiohttp.websocket import WS_KEY, Message
from aiohttp.websocket import WebSocketParser, WebSocketWriter, WebSocketError
from aiohttp.websocket import (MSG_BINARY, MSG_TEXT, MSG_CLOSE, MSG_PING,
    MSG_PONG)
from aiohttp.websocket_client import (MsgType, closedMessage,
    ClientWebSocketResponse)

from aiogremlin.abc import AbstractFactory, AbstractConnection
from aiogremlin.exceptions import SocketClientError
from aiogremlin.log import INFO, logger


# This is temporary until aiohttp pull #367 is merged/released.
@asyncio.coroutine
def ws_connect(url, protocols=(), timeout=10.0, connector=None,
               response_class=None, autoclose=True, autoping=True, loop=None):
    """Initiate websocket connection."""
    if loop is None:
        loop = asyncio.get_event_loop()

    sec_key = base64.b64encode(os.urandom(16))

    headers = {
        hdrs.UPGRADE: hdrs.WEBSOCKET,
        hdrs.CONNECTION: hdrs.UPGRADE,
        hdrs.SEC_WEBSOCKET_VERSION: '13',
        hdrs.SEC_WEBSOCKET_KEY: sec_key.decode(),
    }
    if protocols:
        headers[hdrs.SEC_WEBSOCKET_PROTOCOL] = ','.join(protocols)

    # send request
    resp = yield from client.request(
        'get', url, headers=headers,
        read_until_eof=False,
        connector=connector, loop=loop)

    # check handshake
    if resp.status != 101:
        raise WSServerHandshakeError('Invalid response status')

    if resp.headers.get(hdrs.UPGRADE, '').lower() != 'websocket':
        raise WSServerHandshakeError('Invalid upgrade header')

    if resp.headers.get(hdrs.CONNECTION, '').lower() != 'upgrade':
        raise WSServerHandshakeError('Invalid connection header')

    # key calculation
    key = resp.headers.get(hdrs.SEC_WEBSOCKET_ACCEPT, '')
    match = base64.b64encode(hashlib.sha1(sec_key + WS_KEY).digest()).decode()
    if key != match:
        raise WSServerHandshakeError('Invalid challenge response')

    # websocket protocol
    protocol = None
    if protocols and hdrs.SEC_WEBSOCKET_PROTOCOL in resp.headers:
        resp_protocols = [proto.strip() for proto in
                          resp.headers[hdrs.SEC_WEBSOCKET_PROTOCOL].split(',')]

        for proto in resp_protocols:
            if proto in protocols:
                protocol = proto
                break

    reader = resp.connection.reader.set_parser(WebSocketParser)
    writer = WebSocketWriter(resp.connection.writer, use_mask=True)

    if response_class is None:
        response_class = ClientWebSocketResponse

    return response_class(
        reader, writer, protocol, resp, timeout, autoclose, autoping, loop)


class BaseFactory(AbstractFactory):

    @property
    def factory(self):
        return self


class AiohttpFactory(BaseFactory):

    @classmethod
    @asyncio.coroutine
    def connect(cls, uri='ws://localhost:8182/', pool=None, protocols=(),
                connector=None, autoclose=False, autoping=True, loop=None):
        if pool:
            loop = loop or pool.loop
        try:
            return (yield from ws_connect(
                uri, protocols=protocols, connector=connector,
                response_class=GremlinClientWebSocketResponse,
                autoclose=True, autoping=True, loop=loop))
        except WSServerHandshakeError as e:
            raise SocketClientError(e.message)


class BaseConnection(AbstractConnection):

    def __init__(self, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._parser = StreamParser(
            buf=DataQueue(loop=self._loop), loop=self._loop)

    @property
    def parser(self):
        return self._parser


class GremlinClientWebSocketResponse(BaseConnection, ClientWebSocketResponse):

    def __init__(self, reader, writer, protocol, response, timeout, autoclose,
                 autoping, loop):
        BaseConnection.__init__(self, loop=loop)
        ClientWebSocketResponse.__init__(self, reader, writer, protocol,
            response, timeout, autoclose, autoping, loop)

    @property
    def closed(self):
        """Required by ABC."""
        return self._closed

    @asyncio.coroutine
    def close(self, *, code=1000, message=b''):
        if not self._closed:
            closed = self._close()
            if closed:
                return True
            while True:
                try:
                    msg = yield from asyncio.wait_for(
                        self._reader.read(), self._timeout, loop=self._loop)
                except asyncio.CancelledError:
                    self._close_code = 1006
                    self._response.close(force=True)
                    raise
                except Exception as exc:
                    self._close_code = 1006
                    self._exception = exc
                    self._response.close(force=True)
                    return True

                if msg.tp == MsgType.close:
                    self._close_code = msg.data
                    self._response.close(force=True)
                    return True
        else:
            return False

    def _close(self):
        self._closed = True
        try:
            self._writer.close(code, message)
        except asyncio.CancelledError:
            self._close_code = 1006
            self._response.close(force=True)
            raise
        except Exception as exc:
            self._close_code = 1006
            self._exception = exc
            self._response.close(force=True)
            return True

        if self._closing:
            self._response.close(force=True)
            return True

    def send(self, message, binary=True):
        if binary:
            method = self.send_bytes
        else:
            method = self.send_str
        try:
            method(message)
        except RuntimeError:
            # Socket closed.
            raise
        except TypeError:
            # Bytes/string input error.
            raise

    @asyncio.coroutine
    def receive(self):
        if self._waiting:
            raise RuntimeError('Concurrent call to receive() is not allowed')

        self._waiting = True
        try:
            while True:
                if self._closed:
                    return closedMessage

                try:
                    msg = yield from self._reader.read()
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    raise
                except WebSocketError as exc:
                    self._close_code = exc.code
                    yield from self.close(code=exc.code)
                    raise
                except Exception as exc:
                    self._exception = exc
                    self._closing = True
                    self._close_code = 1006
                    yield from self.close()
                    raise
                if msg.tp == MsgType.close:
                    self._closing = True
                    self._close_code = msg.data
                    if not self._closed and self._autoclose:
                        yield from self.close()
                    raise RuntimeError("Socket connection closed by server.")
                elif not self._closed:
                    if msg.tp == MsgType.ping and self._autoping:
                        self._writer.pong(msg.data)
                    elif msg.tp == MsgType.pong and self._autoping:
                        continue
                    else:
                        if msg.tp == MsgType.binary:
                            self.parser.feed_data(msg.data.decode())
                        elif msg.tp == MsgType.text:
                            self.parser.feed_data(msg.data.strip())
                        break
        finally:
            self._waiting = False
