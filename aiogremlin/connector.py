"""Websocket connection factory and manager."""

import asyncio

from aiowebsocketclient import WebSocketConnector

from aiogremlin.response import GremlinClientWebSocketResponse

__all__ = ("GremlinConnector",)


class GremlinConnector(WebSocketConnector):
    """Create and manage reusable websocket connections. Out of the box
    support for multiple enpoints (databases).

    :param float conn_timeout: timeout for establishing connection (seconds)
        (optional). Values ``0`` or ``None`` mean no timeout
    :param bool force_close: close websockets after release
    :param int limit: limit for total open websocket connections
    :param aiohttp.client.ClientSession client_session: Underlying HTTP
        session used to establish websocket connections
    :param loop: `event loop` If param is ``None``, `asyncio.get_event_loop`
        is used for getting default event loop (optional)
    :param ws_response_class: WebSocketResponse class implementation.
        ``ClientWebSocketResponse`` by default
    :param bool verbose: Set log level to info. False by default
    """
    def __init__(self, *, conn_timeout=None, force_close=False, limit=1024,
                 client_session=None, loop=None, verbose=False):

        super().__init__(conn_timeout=conn_timeout, force_close=force_close,
                         limit=limit, client_session=client_session, loop=loop,
                         ws_response_class=GremlinClientWebSocketResponse)
