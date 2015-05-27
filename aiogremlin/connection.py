"""
"""
import asyncio
import base64
import hashlib
import os

import aiohttp

from aiohttp.websocket_client import ClientWebSocketResponse
from aiogremlin.exceptions import SocketClientError
from aiogremlin.log import INFO, logger

__all__ = ('GremlinFactory', 'GremlinClientWebSocketResponse')


class GremlinClientWebSocketResponse(ClientWebSocketResponse):

    def __init__(self, reader, writer, protocol, response, timeout, autoclose,
                 autoping, loop):
        ClientWebSocketResponse.__init__(self, reader, writer, protocol,
                                         response, timeout, autoclose,
                                         autoping, loop)
        self._parser = aiohttp.StreamParser(buf=aiohttp.DataQueue(loop=loop),
                                            loop=loop)

    @property
    def parser(self):
        return self._parser

    @asyncio.coroutine
    def close(self, *, code=1000, message=b''):
        if not self._closed:
            did_close = self._close()
            if did_close:
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

                if msg.tp == aiohttp.MsgType.close:
                    self._close_code = msg.data
                    self._response.close(force=True)
                    return True
        else:
            return False

    def _close(self, code=1000, message=b''):
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
        msg = yield from super().receive()
        if msg.tp == aiohttp.MsgType.binary:
            self.parser.feed_data(msg.data.decode())
        elif msg.tp == aiohttp.MsgType.text:
            self.parser.feed_data(msg.data.strip())
        else:
            if msg.tp == aiohttp.MsgType.close:
                yield from ws.close()
            elif msg.tp == aiohttp.MsgType.error:
                raise msg.data
            elif msg.tp == aiohttp.MsgType.closed:
                pass


class GremlinFactory:

    def __init__(self, connector=None, loop=None):
        self._connector = connector
        self._loop = loop or asyncio.get_event_loop()

    @asyncio.coroutine
    def ws_connect(self, url='ws://localhost:8182/', protocols=(),
                   autoclose=False, autoping=True):
        try:
            return (yield from aiohttp.ws_connect(
                url, protocols=protocols, connector=self._connector,
                ws_response_class=GremlinClientWebSocketResponse,
                autoclose=True, autoping=True, loop=self._loop))
        except aiohttp.WSServerHandshakeError as e:
            raise SocketClientError(e.message)
