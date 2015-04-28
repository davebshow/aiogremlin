"""
"""
import asyncio
import json
import ssl
import uuid

from .connection import WebsocketPool
from .log import client_logger
from .protocol import gremlin_response_parser, GremlinWriter
from .response import GremlinResponse
from .tasks import async


class GremlinBase:

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

class GremlinClient(GremlinBase):

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
    def send(self, gremlin, connection=None, bindings=None, lang=None,
             op=None, processor=None, binary=True):
        """
        """
        lang = lang or self.lang
        op = op or self.op
        processor = processor or self.processor
        message = json.dumps({
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
        yield from writer.send(message, binary=binary)
        return connection

    @asyncio.coroutine
    def submit(self, gremlin, bindings=None, lang=None,
               op=None, processor=None, consumer=None, collect=True, **kwargs):
        """
        """
        lang = lang or self.lang
        op = op or self.op
        processor = processor or self.processor
        connection = yield from self.send(gremlin, bindings=bindings, lang=lang,
                op=op, processor=processor)
        results = yield from self.run(connection, consumer=consumer,
            collect=collect)
        return results

    def s(self, *args, **kwargs):
        """
        """
        if not kwargs.get("loop", ""):
            kwargs["loop"] = self.loop
        return async(self.submit, *args, **kwargs)

    @asyncio.coroutine
    def recv(self, connection):
        """
        """
        return (yield from gremlin_response_parser(connection))

    @asyncio.coroutine
    def run(self, connection, consumer=None, collect=True):
        """
        """
        results = []
        while True:
            message = yield from self.recv(connection)
            if message is None:
                break
            message = GremlinResponse(message)
            if consumer:
                message = consumer(message)
                if asyncio.iscoroutine(message):
                    message = yield from asyncio.async(message, loop=self.loop)
            if message and collect:
                results.append(message)
        return results
