import asyncio

from contextlib import contextmanager

from aiowebsocketclient import WebSocketConnector

from aiogremlin.response import GremlinClientWebSocketResponse
from aiogremlin.contextmanager import ConnectionContextManager
from aiogremlin.log import logger

__all__ = ("GremlinConnector",)


class GremlinConnector(WebSocketConnector):

    def __init__(self, *, conn_timeout=None, force_close=False, limit=1024,
                 client_session=None, loop=None):
        """
        :param float conn_timeout: timeout for establishing connection
                                   (optional). Values ``0`` or ``None``
                                   mean no timeout
        :param bool force_close: close underlying sockets after
                                 releasing connection
        :param int limit: limit for total open websocket connections
        :param aiohttp.client.ClientSession client_session: Underlying HTTP
                                                            session used to
                                                            to establish
                                                            websocket
                                                            connections
        :param loop: `event loop`
                     used for processing HTTP requests.
                     If param is ``None``, `asyncio.get_event_loop`
                     is used for getting default event loop.
                     (optional)
        :param ws_response_class: WebSocketResponse class implementation.
                                  ``ClientWebSocketResponse`` by default
        """
        super().__init__(conn_timeout=conn_timeout, force_close=force_close,
                         limit=limit, client_session=client_session, loop=loop,
                         ws_response_class=GremlinClientWebSocketResponse)

    @contextmanager
    @asyncio.coroutine
    def connection(self, url, *,
                   protocols=(),
                   timeout=10.0,
                   autoclose=True,
                   autoping=True):
        ws = yield from self.ws_connect(url='ws://localhost:8182/')
        return ConnectionContextManager(ws)

    # aioredis style
    def __enter__(self):
        raise RuntimeError(
            "'yield from' should be used as a context manager expression")

    def __exit__(self, *args):
        pass

    def __iter__(self):
        ws = yield from self.ws_connect(url='ws://localhost:8182/')
        return ConnectionContextManager(ws)
