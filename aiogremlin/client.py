"""Client for the Tinkerpop 3 Gremlin Server."""

import asyncio
import ssl

import aiohttp

from aiogremlin.connection import (GremlinFactory,
                                   GremlinClientWebSocketResponse)
from aiogremlin.exceptions import RequestError
from aiogremlin.log import logger, INFO
from aiogremlin.pool import WebSocketPool
from aiogremlin.subprotocol import gremlin_response_parser, GremlinWriter

__all__ = ("create_client", "GremlinClient", "GremlinResponse",
           "GremlinResponseStream")


@asyncio.coroutine
def create_client(*, url='ws://localhost:8182/', loop=None,
                  protocol=None, lang="gremlin-groovy", op="eval",
                  processor="", pool=None, factory=None, poolsize=10,
                  timeout=None, verbose=False, fill_pool=True, connector=None):

    if factory is None:
        factory = aiohttp.ClientSession(
            connector=connector,
            ws_response_class=GremlinClientWebSocketResponse,
            loop=loop)

    if pool is None:
        pool = WebSocketPool(url,
                             factory=factory,
                             poolsize=poolsize,
                             timeout=timeout,
                             loop=loop,
                             verbose=verbose)

    if fill_pool:
        yield from pool.fill_pool()

    return GremlinClient(url=url,
                         loop=loop,
                         protocol=protocol,
                         lang=lang,
                         op=op,
                         processor=processor,
                         pool=pool,
                         factory=factory,
                         verbose=verbose)


class GremlinClient:

    def __init__(self, url='ws://localhost:8182/', loop=None,
                 protocol=None, lang="gremlin-groovy", op="eval",
                 processor="", pool=None, factory=None, poolsize=10,
                 timeout=None, verbose=False, connector=None,
                 connection=None):
        """
        """
        self.url = url
        self.ssl = ssl
        self.protocol = protocol
        self._loop = loop or asyncio.get_event_loop()
        self.lang = lang or "gremlin-groovy"
        self.op = op or "eval"
        self.processor = processor or ""
        self.poolsize = poolsize
        self.timeout = timeout
        self._pool = pool
        self._connector = connector
        self._conn = connection
        if pool is not None:
            factory = pool._factory
            self._connected = self._pool._connected
        elif self._conn and not getattr(connection, "closed", True):
            self._connected = True
        else:
            self._connected = False
            self._conn = asyncio.async(self._connect(), loop=self._loop)
        self._factory = factory or GremlinFactory(connector=self._connector,
                                                  loop=self._loop)
        if verbose:
            logger.setLevel(INFO)

    @property
    def loop(self):
        return self._loop

    @asyncio.coroutine
    def close(self):
        try:
            if self._pool:
                yield from self._pool.close()
            elif self._connected:
                yield from self._conn.close()
        finally:
            self._connected = False

    @asyncio.coroutine
    def _connect(self):
        """
        """
        connection = yield from self._factory.ws_connect(self.url)
        self._connected = True
        return connection

    @asyncio.coroutine
    def _acquire(self):
        if self._pool:
            conn = yield from self._pool.acquire()
        elif self._connected:
            conn = self._conn
        else:
            try:
                self._conn = yield from self._conn
            except TypeError:
                self._conn = yield from self._connect()
            except Exception:
                raise RuntimeError("Unable to acquire connection.")
            conn = self._conn
        return conn

    @asyncio.coroutine
    def submit(self, gremlin, *, connection=None, bindings=None, lang=None,
               op=None, processor=None, session=None, binary=True):
        """
        """
        lang = lang or self.lang
        op = op or self.op
        processor = processor or self.processor
        if connection is None:
            connection = yield from self._acquire()
        writer = GremlinWriter(connection)
        connection = writer.write(gremlin, bindings=bindings, lang=lang, op=op,
                                  processor=processor, session=session,
                                  binary=binary)
        return GremlinResponse(connection,
                               pool=self._pool,
                               session=session,
                               loop=self._loop)

    @asyncio.coroutine
    def execute(self, gremlin, *, bindings=None, lang=None,
                op=None, processor=None, consumer=None, collect=True):
        """
        """
        lang = lang or self.lang
        op = op or self.op
        processor = processor or self.processor
        resp = yield from self.submit(gremlin, bindings=bindings, lang=lang,
                                      op=op, processor=processor)
        return (yield from resp.get())


class GremlinResponse:

    def __init__(self, conn, *, pool=None, session=None, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._session = session
        self._stream = GremlinResponseStream(conn, pool=pool, loop=self._loop)

    @property
    def stream(self):
        return self._stream

    @property
    def session(self):
        return self._session

    @asyncio.coroutine
    def get(self):
        return (yield from self._run())

    @asyncio.coroutine
    def _run(self):
        """
        """
        results = []
        while True:
            message = yield from self._stream.read()
            if message is None:
                break
            results.append(message)
        return results


class GremlinResponseStream:

    def __init__(self, conn, pool=None, loop=None):
        self._conn = conn
        self._pool = pool
        self._loop = loop or asyncio.get_event_loop()
        data_stream = aiohttp.DataQueue(loop=self._loop)
        self._stream = self._conn.parser.set_parser(gremlin_response_parser,
                                                    output=data_stream)

    @asyncio.coroutine
    def read(self):
        if self._stream.at_eof():
            if self._pool:
                self._pool.release(self._conn)
            message = None
        else:
            asyncio.async(self._conn.receive(), loop=self._loop)
            try:
                message = yield from self._stream.read()
            except RequestError:
                if self._pool:
                    self._pool.release(self._conn)
        return message
