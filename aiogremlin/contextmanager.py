from contextlib import contextmanager
from aiogremlin.client import GremlinBase, GremlinClient
from aiogremlin.connection import WebsocketPool


class GremlinContext(GremlinBase):
    # Untested.
    @property
    def client(self):
        return self._client()

    @property
    def pool(self):
        return self._pool()

    @contextmanager
    def _client(self):
        client = GremlinClient(uri=self.uri, loop=self._loop, ssl=self.ssl,
            protocol=self.protocol, lang=self.lang, op=self.op,
            processor=self.processor, pool=self.pool, factory=self.factory,
            poolsize=self.poolsize, timeout=self.timeout)
        try:
            yield client
        finally:
            yield from client.close()

    @contextmanager
    def _pool(self):
        pool = WebsocketPool(uri=self.uri, loop=self._loop,
            factory=self.factory, poolsize=self.poolsize, timeout=self.timeout)
        try:
            yield pool
        finally:
            yield from pool.close()
