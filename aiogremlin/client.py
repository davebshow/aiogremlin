"""Client for the Tinkerpop 3 Gremlin Server."""

import asyncio

import aiohttp

from aiogremlin.response import GremlinClientWebSocketResponse
from aiogremlin.exceptions import RequestError
from aiogremlin.log import logger, INFO
from aiogremlin.connector import GremlinConnector
from aiogremlin.subprotocol import gremlin_response_parser, GremlinWriter

__all__ = ("GremlinClient", "GremlinClientSession")


@asycnio.coroutine
def submit(gremlin, *,
           url='ws://localhost:8182/',
           bindings=None,
           lang="gremlin-groovy",
           op="eval",
           processor="",
           connector=None):

    connector = aiohttp.TCPConnector(force_close=True)

    client_session = aiohttp.ClientSession(
        connector=connector, ws_response_class=GremlinClientWebSocketResponse)

    gremlin_client = GremlinClient(url=url, connector=client_session)

    try:
        resp = yield from gremlin_client.submit(
            gremlin, bindings=bindings, lang=lang, op=op, processor=processor)

        return resp

    finally:
        gremlin_client.detach()
        client_session.detach()


class SimpleGremlinClient:

    def __init__(self, connection, *, loop=None, verbose=False):
        """This class is primarily designed to be used in the context
        `manager"""
        self._loop = loop or asyncio.get_event_loop()
        self._connection = connection
        if verbose:
            logger.setLevel(INFO)

    @asyncio.coroutine
    def submit(self, gremlin, *, bindings=None, lang="gremlin-groovy",
               op="eval", processor=""):
        """
        """
        writer = GremlinWriter(self._connection)

        connection = writer.write(gremlin, bindings=bindings, lang=lang, op=op,
                                  processor=processor, session=session,
                                  binary=binary)

        return GremlinResponse(self._connection,
                               pool=self._pool,
                               session=session,
                               loop=self._loop)


class GremlinClient:

    def __init__(self, url='ws://localhost:8182/', loop=None,
                 protocols=None, lang="gremlin-groovy", op="eval",
                 processor="", timeout=None, verbose=False,
                 session=None, connector=None):
        """
        """
        # Maybe getter setter for some of these: url, session, lang, op
        self.url = url
        self._loop = loop or asyncio.get_event_loop()
        self.lang = lang or "gremlin-groovy"
        self.op = op or "eval"
        self.processor = processor or ""
        self._timeout = timeout
        self._session = session
        if verbose:
            logger.setLevel(INFO)
        if connector is None:
            connector = GremlinConnector()
        self._connector = connector

    @property
    def loop(self):
        return self._loop

    @property
    def closed(self):
        return self._closed or self._connector is None

    @asyncio.coroutine
    def close(self):

        if self._closed:
            return

        self._closed = True

        try:
            yield from self._connector.close()
        finally:
            self._connector = None

    def detach(self):
        self._connector = None

    @asyncio.coroutine
    def submit(self, gremlin, *, bindings=None, lang=None,
               op=None, processor=None, binary=True):
        """
        """
        lang = lang or self.lang
        op = op or self.op
        processor = processor or self.processor

        ws = yield from self._connector.ws_connect(
            self.url, timeout=self._timeout)

        writer = GremlinWriter(ws)

        ws = writer.write(gremlin, bindings=bindings, lang=lang, op=op,
                          processor=processor, binary=binary,
                          session=self._session)

        return GremlinResponse(ws, session=self._session, loop=self._loop)

    @asyncio.coroutine
    def execute(self, gremlin, *, bindings=None, lang=None,
                op=None, processor=None, binary=True):
        """
        """
        lang = lang or self.lang
        op = op or self.op
        processor = processor or self.processor

        resp = yield from self.submit(gremlin, bindings=bindings, lang=lang,
                                      op=op, processor=processor,
                                      binary=binary)

        return (yield from resp.get())


class GremlinClientSession(GremlinClient):

    def __init__(self, url='ws://localhost:8182/', loop=None,
                 protocols=None, lang="gremlin-groovy", op="eval",
                 processor="", timeout=None, verbose=False,
                 session=None, connector=None):

        super().__init__(url=url, loop=loop, protocols=protocols, lang=lang,
                         op=op, processor=processor, timeout=timeout,
                         verbose=verbose, connector=connector)

        if session is None:
            session = str(uuid4.uuid4())
        self._session = session

    def set_session(self):
        pass

    def change_session(self):
        pass


class GremlinResponse:

    def __init__(self, ws, *, session=None, loop=None):
        # Add timeout for read
        self._loop = loop or asyncio.get_event_loop()
        self._session = session
        self._stream = GremlinResponseStream(ws, oop=self._loop)

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

    def __init__(self, ws, loop=None):
        self._ws = ws
        self._loop = loop or asyncio.get_event_loop()
        data_stream = aiohttp.DataQueue(loop=self._loop)
        self._stream = self._ws.parser.set_parser(gremlin_response_parser,
                                                  output=data_stream)

    @asyncio.coroutine
    def read(self):
        if self._stream.at_eof():
            yield from self._ws.release()
            message = None
        else:
            asyncio.async(self._ws.receive(), loop=self._loop)
            try:
                message = yield from self._stream.read()
            except RequestError:
                yield from self._ws.release()
        return message
