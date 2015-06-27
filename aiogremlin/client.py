"""Client for the Tinkerpop 3 Gremlin Server."""

import asyncio
import uuid

import aiohttp

from aiogremlin.response import GremlinClientWebSocketResponse
from aiogremlin.exceptions import RequestError
from aiogremlin.log import logger, INFO
from aiogremlin.connector import GremlinConnector
from aiogremlin.subprotocol import gremlin_response_parser, GremlinWriter

__all__ = ("submit", "SimpleGremlinClient", "GremlinClient",
           "GremlinClientSession")


class BaseGremlinClient:

    def __init__(self, *, lang="gremlin-groovy", op="eval", processor="",
                 loop=None, verbose=False):
        self._lang = lang
        self._op = op
        self._processor = processor
        self._loop = loop or asyncio.get_event_loop()
        self._closed = False
        if verbose:
            logger.setLevel(INFO)

    @property
    def loop(self):
        return self._loop

    @property
    def op(self):
        return self._op

    @property
    def processor(self):
        return self._processor

    @property
    def lang(self):
        return self._lang

    def submit(self):
        raise NotImplementedError

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


class SimpleGremlinClient(BaseGremlinClient):

    def __init__(self, connection, *, lang="gremlin-groovy", op="eval",
                 processor="", loop=None, verbose=False):
        """This class is primarily designed to be used in the context
        `manager"""
        super().__init__(lang=lang, op=op, processor=processor, loop=loop,
                         verbose=verbose)
        self._connection = connection

    @asyncio.coroutine
    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            yield from self._connection.release()
        finally:
            self._connection = None

    @property
    def closed(self):
        return (self._closed or self._connection.closed or
                self._connection is None)

    @asyncio.coroutine
    def submit(self, gremlin, *, bindings=None, lang="gremlin-groovy",
               op="eval", processor="", session=None, binary=True):
        """
        """
        writer = GremlinWriter(self._connection)

        connection = writer.write(gremlin, bindings=bindings, lang=lang, op=op,
                                  processor=processor, session=session,
                                  binary=binary)

        return GremlinResponse(self._connection,
                               session=session,
                               loop=self._loop)


class GremlinClient(BaseGremlinClient):

    def __init__(self, *, url='ws://localhost:8182/', loop=None,
                 protocols=None, lang="gremlin-groovy", op="eval",
                 processor="", timeout=None, verbose=False, connector=None):
        """
        """
        super().__init__(lang=lang, op=op, processor=processor, loop=loop,
                         verbose=verbose)
        self._url = url
        self._timeout = timeout
        self._session = None
        if connector is None:
            connector = GremlinConnector(loop=self._loop)
        self._connector = connector

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

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


class GremlinClientSession(GremlinClient):

    def __init__(self, *, url='ws://localhost:8182/', loop=None,
                 protocols=None, lang="gremlin-groovy", op="eval",
                 processor="session", session=None, timeout=None,
                 verbose=False, connector=None):
        """
        """
        super().__init__(url=url, protocols=protocols, lang=lang, op=op,
                         processor=processor, loop=loop, timeout=timeout,
                         verbose=verbose, connector=connector)

        if session is None:
            session = str(uuid.uuid4())
        self._session = session

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, value):
        self._session = value

    def reset_session(self, session=None):
        if session is None:
            session = str(uuid.uuid4())
        self._session = session
        return self._session


class GremlinResponse:

    def __init__(self, ws, *, session=None, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._session = session
        self._stream = GremlinResponseStream(ws, loop=self._loop)

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
                raise
        return message


@asyncio.coroutine
def submit(gremlin, *,
           url='ws://localhost:8182/',
           bindings=None,
           lang="gremlin-groovy",
           op="eval",
           processor="",
           connector=None,
           loop=None):

    if loop is None:
        loop = asyncio.get_event_loop()

    connector = aiohttp.TCPConnector(force_close=True, loop=loop)

    client_session = aiohttp.ClientSession(
        connector=connector, loop=loop,
        ws_response_class=GremlinClientWebSocketResponse)

    gremlin_client = GremlinClient(url=url, loop=loop,
                                   connector=client_session)

    try:
        resp = yield from gremlin_client.submit(
            gremlin, bindings=bindings, lang=lang, op=op, processor=processor)

        return resp

    finally:
        gremlin_client.detach()
        client_session.detach()
