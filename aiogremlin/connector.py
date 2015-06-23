import asyncio

from aiowebsocketclient import WebSocketConnector

from aiogremlin.response import GremlinClientWebSocketResponse
from aiogremlin.contextmanager import ConnectionContextManager
from aiogremlin.log import logger

__all__ = ("GremlinConnector",)


class GremlinConnector(WebSocketConnector):

    def __init__(self, *args, **kwargs):
        kwargs["ws_response_class"] = GremlinClientWebSocketResponse
        super().__init__(*args, **kwargs)

    @asyncio.coroutine
    def create_client(self, *, url='ws://localhost:8182/', loop=None,
                      protocol=None, lang="gremlin-groovy", op="eval",
                      processor="", verbose=False):

        return GremlinClient(url=url,
                             loop=loop,
                             protocol=protocol,
                             lang=lang,
                             op=op,
                             processor=processor,
                             connector=self
                             verbose=verbose)

    def create_client_session(self, *, url='ws://localhost:8182/', loop=None,
                              protocol=None, lang="gremlin-groovy", op="eval",
                              processor="", connector=self, verbose=False):

        return GremlinClientSession(url=url,
                                    loop=loop,
                                    protocol=protocol,
                                    lang=lang,
                                    op=op,
                                    processor=processor,
                                    connector=self
                                    verbose=verbose)

    # # Something like
    # @contextmanager
    # @asyncio.coroutine
    # def connect(self, url, etc):
    #     pass

    # aioredis style
    def __enter__(self):
        raise RuntimeError(
            "'yield from' should be used as a context manager expression")

    def __exit__(self, *args):
        pass

    def __iter__(self):
        conn = yield from self.ws_connect(url='ws://localhost:8182/')
        return ConnectionContextManager(client)
