"""Client for the Tinkerpop 3 Gremlin Server."""

import asyncio
import ssl
import uuid

import aiohttp
import ujson

from aiogremlin.connection import WebsocketPool
from aiogremlin.log import client_logger
from aiogremlin.protocol import gremlin_response_parser, GremlinWriter


@asyncio.coroutine
def create_client(uri='ws://localhost:8182/', loop=None, ssl=None,
                  protocol=None, lang="gremlin-groovy", op="eval",
                  processor="", pool=None, factory=None, poolsize=10,
                  timeout=None, **kwargs):
    pool = WebsocketPool(uri,
                         factory=factory,
                         poolsize=poolsize,
                         timeout=timeout,
                         loop=loop)

    yield from pool.init_pool()

    return GremlinClient(uri=uri,
                         loop=loop,
                         ssl=ssl,
                         protocol=protocol,
                         lang=lang,
                         op=op,
                         processor=processor,
                         pool=pool,
                         factory=factory)


class GremlinClient:

    def __init__(self, uri='ws://localhost:8182/', loop=None, ssl=None,
                 protocol=None, lang="gremlin-groovy", op="eval",
                 processor="", pool=None, factory=None, poolsize=10,
                 timeout=None, **kwargs):
        """
        """
        self.uri = uri
        self.ssl = ssl
        self.protocol = protocol
        # if self.ssl:
        #     protocol = protocol or ssl.PROTOCOL_TLSv1
        #     ssl_context = ssl.SSLContext(protocol)
        #     ssl_context.load_verify_locations(ssl)
        #     ssl_context.verify_mode = ssl.CERT_REQUIRED
        #     self.ssl_context = ssl_context  # This will go to conn pool... use TCPConnector?
        self._loop = loop or asyncio.get_event_loop()
        self.lang = lang or "gremlin-groovy"
        self.op = op or "eval"
        self.processor = processor or ""
        self.poolsize = poolsize
        self.timeout = timeout
        self.pool = pool or WebsocketPool(uri, factory=factory,
            poolsize=poolsize, timeout=timeout, loop=self._loop)
        self.factory = factory or self.pool.factory

    @property
    def loop(self):
        return self._loop

    @asyncio.coroutine
    def close(self):
        yield from self.pool.close()

    @asyncio.coroutine
    def connect(self, **kwargs):
        """
        """
        loop = kwargs.get("loop", "") or self.loop
        connection = yield from self.factory.connect(self.uri, loop=loop,
            **kwargs)
        return connection

    @asyncio.coroutine
    def submit(self, gremlin, connection=None, bindings=None, lang=None,
               op=None, processor=None, binary=True):
        """
        """
        lang = lang or self.lang
        op = op or self.op
        processor = processor or self.processor
        message = ujson.dumps({
            "requestId": str(uuid.uuid4()),
            "op": op,
            "processor": processor,
            "args":{
                "gremlin": gremlin,
                "bindings": bindings,
                "language":  lang
            }
        })
        if connection is None:
            connection = yield from self.pool.connect(self.uri, loop=self.loop)
        writer = GremlinWriter(connection)
        connection = yield from writer.write(message, binary=binary)
        queue = connection.parser.set_parser(gremlin_response_parser,
            output=aiohttp.DataQueue(loop=self._loop))
        return GremlinResponse(connection, queue, loop=self._loop)

    @asyncio.coroutine
    def execute(self, gremlin, bindings=None, lang=None,
               op=None, processor=None, consumer=None, collect=True, **kwargs):
        """
        """
        lang = lang or self.lang
        op = op or self.op
        processor = processor or self.processor
        resp = yield from self.submit(gremlin, bindings=bindings, lang=lang,
                op=op, processor=processor)
        return (yield from resp.get())


class GremlinResponse:

    def __init__(self, conn, queue, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._stream = GremlinResponseStream(conn, queue, loop=self._loop)

    @property
    def stream(self):
        return self._stream

    @asyncio.coroutine
    def get(self):
        return (yield from self._run())

    @asyncio.coroutine
    def _run(self):
        """
        """
        results = []
        while True:
            message = yield from self.stream.read()
            if message is None:
                break
            results.append(message)
        return results


class GremlinResponseStream:

    def __init__(self, conn, queue, loop=None):
        self._conn = conn
        self._queue = queue
        self._loop = loop or asyncio.get_event_loop()

    @asyncio.coroutine
    def _read(self):
        message = asyncio.async(self._queue.read(), loop=self._loop)
        done, pending = yield from asyncio.wait(
            [message, asyncio.async(self._conn._receive(), loop=self._loop)],
            loop=self._loop, return_when=asyncio.FIRST_COMPLETED)
        if message in done:
            try:
                return message.result()
            except aiohttp.streams.EofStream:
                self._conn.feed_pool()
            except Exception:
                self._conn.feed_pool()
                raise
        else:
            message.cancel()

    @asyncio.coroutine
    def read(self):
        return (yield from self._read())
