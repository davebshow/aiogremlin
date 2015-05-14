"""Client for the Tinkerpop 3 Gremlin Server."""

import asyncio
import ssl
import uuid

import aiohttp

from aiogremlin.connection import WebsocketPool
from aiogremlin.log import client_logger, INFO
from aiogremlin.protocol import gremlin_response_parser, GremlinWriter


@asyncio.coroutine
def create_client(uri='ws://localhost:8182/', loop=None, ssl=None,
                  protocol=None, lang="gremlin-groovy", op="eval",
                  processor="", pool=None, factory=None, poolsize=10,
                  timeout=None, verbose=False, **kwargs):
    pool = WebsocketPool(uri,
                         factory=factory,
                         poolsize=poolsize,
                         timeout=timeout,
                         loop=loop,
                         verbose=verbose)

    yield from pool.init_pool()

    return GremlinClient(uri=uri,
                         loop=loop,
                         ssl=ssl,
                         protocol=protocol,
                         lang=lang,
                         op=op,
                         processor=processor,
                         pool=pool,
                         factory=factory,
                         verbose=verbose)


class GremlinClient:

    def __init__(self, uri='ws://localhost:8182/', loop=None, ssl=None,
                 protocol=None, lang="gremlin-groovy", op="eval",
                 processor="", pool=None, factory=None, poolsize=10,
                 timeout=None, verbose=True, **kwargs):
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
        if verbose:
            client_logger.setLevel(INFO)

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
               op=None, processor=None, session=None, binary=True):
        """
        """
        lang = lang or self.lang
        op = op or self.op
        processor = processor or self.processor
        message = {
            "requestId": str(uuid.uuid4()),
            "op": op,
            "processor": processor,
            "args":{
                "gremlin": gremlin,
                "bindings": bindings,
                "language":  lang
            }
        }
        if processor == "session":
            session = session or str(uuid.uuid4())
            message["args"]["session"] = session
            client_logger.info(
                "Session ID: {}".format(message["args"]["session"]))
        if connection is None:
            connection = yield from self.pool.connect(self.uri, loop=self.loop)
        writer = GremlinWriter(connection)
        connection = yield from writer.write(message, binary=binary)
        return GremlinResponse(connection, session=session, loop=self._loop)

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

    def __init__(self, conn, session=None, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._session = session
        self._stream = GremlinResponseStream(conn, loop=self._loop)

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

    def __init__(self, conn, loop=None):
        self._conn = conn
        self._loop = loop or asyncio.get_event_loop()
        data_stream = aiohttp.DataQueue(loop=self._loop)
        self._stream = self._conn.parser.set_parser(gremlin_response_parser,
                                                    output=data_stream)

    @asyncio.coroutine
    def read(self):
        # For 3.0.0.M9
        # if self._stream.at_eof():
        #     self._conn.feed_pool()
        #     message = None
        # else:
        # This will be different 3.0.0.M9
        yield from self._conn._receive()
        if self._stream.is_eof():
            self._conn.feed_pool()
            message = None
        else:
            message = yield from self._stream.read()
        return message
