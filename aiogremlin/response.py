"""
Class used to pass messages with the Gremlin Server.
"""

import asyncio
import base64
import hashlib
import os

import aiohttp

from aiowebsocketclient.connector import ClientWebSocketResponse

__all__ = ('GremlinClientWebSocketResponse',)


class GremlinClientWebSocketResponse(ClientWebSocketResponse):
    """Wraps :py:class:`aiohttp.websocket_client.ClientWebSocketResponse`
    with minimal added functionality for the Gremln Server use case.
    """
    def __init__(self, reader, writer, protocol, response, timeout, autoclose,
                 autoping, loop):
        ClientWebSocketResponse.__init__(self, reader, writer, protocol,
                                         response, timeout, autoclose,
                                         autoping, loop)
        self._parser = aiohttp.StreamParser(buf=aiohttp.DataQueue(loop=loop),
                                            loop=loop)

    @property
    def parser(self):
        """
        Read-only property.

        :returns: :py:class:`aiohttp.parsers.StreamParser`
        """
        return self._parser

    @asyncio.coroutine
    def _close(self, *, code=1000, message=b''):
        if not self._closed:
            did_close = self._do_close()
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

    def _do_close(self, code=1000, message=b''):
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

    def send(self, message, *, binary=True):
        """Send a message to the server."""
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
        """
        :ref:`coroutine<coroutine>` method

        Receive a message from the server and push it into the parser.
        """
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
