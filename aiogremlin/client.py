"""Client for the Tinkerpop 3 Gremlin Server."""

import asyncio
import uuid

import aiohttp

from aiogremlin.response import GremlinClientWebSocketResponse
from aiogremlin.exceptions import RequestError, GremlinServerError
from aiogremlin.connector import GremlinConnector
from aiogremlin.subprotocol import gremlin_response_parser, GremlinWriter

__all__ = ("submit", "GremlinClient", "GremlinClientSession",
           "GremlinResponse", "GremlinResponseStream")


class GremlinClient:
    """Main interface for interacting with the Gremlin Server.

    :param str url: url for Gremlin Server (optional). 'http://localhost:8182/'
        by default
    :param loop: :ref:`event loop<asyncio-event-loop>` If param is ``None``,
        `asyncio.get_event_loop` is used for getting default event loop
        (optional)
    :param str lang: Language of scripts submitted to the server.
        "gremlin-groovy" by default
    :param str op: Gremlin Server op argument. "eval" by default.
    :param str processor: Gremlin Server processor argument. "" by default.
    :param float timeout: timeout for websocket read (seconds)(optional).
        Values ``0`` or ``None`` mean no timeout
    :param ws_connector: A class that implements the method ``ws_connect``.
        Usually an instance of ``aiogremlin.connector.GremlinConnector``
    :param float conn_timeout: timeout for establishing connection (seconds)
        (optional). Values ``0`` or ``None`` mean no timeout
    :param username: Username for SASL auth
    :param password: Password for SASL auth
    """

    def __init__(self, *, url='http://localhost:8182/', loop=None,
                 lang="gremlin-groovy", op="eval", processor="",
                 timeout=None, ws_connector=None, client_session=None,
                 conn_timeout=None, username="", password=""):
        self._lang = lang
        self._op = op
        self._processor = processor
        self._loop = loop or asyncio.get_event_loop()
        self._closed = False
        self._session = None
        self._url = url
        self._timeout = timeout
        self._username = username
        self._password = password
        if ws_connector is None:
            ws_connector = GremlinConnector(loop=self._loop,
                                            client_session=client_session,
                                            conn_timeout=conn_timeout)
        self._connector = ws_connector

    @property
    def loop(self):
        """Readonly property that returns event loop used by client"""
        return self._loop

    @property
    def op(self):
        """Readonly property that returns op argument for Gremlin Server"""
        return self._op

    @property
    def processor(self):
        """Readonly property. The processor argument for Gremlin
        Server"""
        return self._processor

    @property
    def lang(self):
        """Readonly property. The language used for Gremlin scripts"""
        return self._lang

    @property
    def url(self):
        """Getter/setter for database url used by the client"""
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    @property
    def closed(self):
        """Readonly property. Return True if client has been closed"""
        return self._closed or self._connector is None

    @asyncio.coroutine
    def close(self):
        """
        :ref:`coroutine<coroutine>` method.

        Close client. If client has not been detached from underlying
        ws_connector, this coroutinemethod closes the latter as well."""
        if self._closed:
            return
        self._closed = True
        try:
            yield from self._connector.close()
        finally:
            self._connector = None

    def detach(self):
        """Detach client from ws_connector. Client status is now closed"""
        self._connector = None

    @asyncio.coroutine
    def submit(self, gremlin, *, bindings=None, lang=None, rebindings=None,
               op=None, processor=None, binary=True, session=None,
               timeout=None):
        """
        :ref:`coroutine<coroutine>` method.

        Submit a script to the Gremlin Server.

        :param str gremlin: Gremlin script to submit to server.
        :param dict bindings: A mapping of bindings for Gremlin script.
        :param str lang: Language of scripts submitted to the server.
            "gremlin-groovy" by default
        :param dict rebindings: Rebind ``Graph`` and ``TraversalSource``
            objects to different variable names in the current request
        :param str op: Gremlin Server op argument. "eval" by default.
        :param str processor: Gremlin Server processor argument. "" by default.
        :param float timeout: timeout for establishing connection (optional).
            Values ``0`` or ``None`` mean no timeout
        :param str session: Session id (optional). Typically a uuid
        :param loop: :ref:`event loop<asyncio-event-loop>` If param is ``None``
            `asyncio.get_event_loop` is used for getting default event loop
            (optional)
        :returns: :py:class:`aiogremlin.client.GremlinResponse` object
        """
        lang = lang or self.lang
        op = op or self.op
        processor = processor or self.processor
        if session is None:
            session = self._session
        if timeout is None:
            timeout = self._timeout

        ws = yield from self._connector.ws_connect(
            self.url, timeout=timeout)

        writer = GremlinWriter(ws)

        ws = writer.write(gremlin=gremlin, bindings=bindings, lang=lang,
                          rebindings=rebindings, op=op,
                          processor=processor, binary=binary,
                          session=session)

        return GremlinResponse(ws, username=self._username,
                               password=self._password, session=session,
                               loop=self._loop)

    @asyncio.coroutine
    def execute(self, gremlin, *, bindings=None, lang=None, rebindings=None,
                session=None, op=None, processor=None, binary=True,
                timeout=None):
        """
        :ref:`coroutine<coroutine>` method.

        Submit a script to the Gremlin Server and get the result.

        :param str gremlin: Gremlin script to submit to server.
        :param dict bindings: A mapping of bindings for Gremlin script.
        :param str lang: Language of scripts submitted to the server.
            "gremlin-groovy" by default
        :param dict rebindings: Rebind ``Graph`` and ``TraversalSource``
            objects to different variable names in the current request
        :param str op: Gremlin Server op argument. "eval" by default.
        :param str processor: Gremlin Server processor argument. "" by default.
        :param float timeout: timeout for establishing connection (optional).
            Values ``0`` or ``None`` mean no timeout
        :param str session: Session id (optional). Typically a uuid
        :param loop: :ref:`event loop<asyncio-event-loop>` If param is ``None``
            `asyncio.get_event_loop` is used for getting default event loop
            (optional)
        :returns: :py:class:`list` of
            :py:class:`aiogremlin.subprotocol.Message`
        """
        lang = lang or self.lang
        op = op or self.op
        processor = processor or self.processor
        resp = yield from self.submit(gremlin, bindings=bindings, lang=lang,
                                      rebindings=rebindings, op=op,
                                      processor=processor, binary=binary,
                                      session=session, timeout=timeout)

        return (yield from resp.get())


class GremlinClientSession(GremlinClient):
    """Interface for interacting with the Gremlin Server using sessions.

    :param str url: url for Gremlin Server (optional). 'http://localhost:8182/'
        by default
    :param loop: :ref:`event loop<asyncio-event-loop>` If param is ``None``,
        `asyncio.get_event_loop` is used for getting default event loop
        (optional)
    :param str lang: Language of scripts submitted to the server.
        "gremlin-groovy" by default
    :param str op: Gremlin Server op argument. "eval" by default.
    :param str processor: Gremlin Server processor argument. "" by default.
    :param float timeout: timeout for establishing connection (optional).
        Values ``0`` or ``None`` mean no timeout
    """

    def __init__(self, *, url='http://localhost:8182/', loop=None,
                 lang="gremlin-groovy", op="eval", processor="session",
                 session=None, timeout=None, client_session=None,
                 ws_connector=None, username="", password=""):
        super().__init__(url=url, lang=lang, op=op, processor=processor,
                         loop=loop, timeout=timeout, ws_connector=ws_connector,
                         client_session=client_session, username=username,
                         password=password)

        if session is None:
            session = str(uuid.uuid4())
        self._session = session

    @property
    def session(self):
        """Getter setter property for session id."""
        return self._session

    @session.setter
    def session(self, value):
        self._session = value

    def reset_session(self, session=None):
        """
        Reset session id.

        :param str session: A unique session id (optional). If None, an id will
            be generated using :py:func:`uuid.uuid4`.

        :returns: New session id.
        """
        if session is None:
            session = str(uuid.uuid4())
        self._session = session
        return self._session


class GremlinResponse:
    """Main interface for reading Gremlin Server responses. Typically returned
    by ``GremlinClient.submit``, not created by user.

    :param ``aiogremlin.response.GremlinClientWebSocketResponse`` ws: Websocket
        connection.
    :param str session: Session id (optional). Typically a uuid
    :param loop: :ref:`event loop<asyncio-event-loop>` If param is ``None``,
        `asyncio.get_event_loop` is used for getting default event loop
        (optional)
    """
    def __init__(self, ws, *, session=None, loop=None, username="",
                 password=""):
        self._loop = loop or asyncio.get_event_loop()
        self._session = session
        self._stream = GremlinResponseStream(ws, username, password,
                                             loop=self._loop)

    @property
    def stream(self):
        """Read-only property used to get data from the stream in chunks.

        :returns: :py:class:`aiogremlin.client.ResponseStream`"""
        return self._stream

    @property
    def session(self):
        """Session ID (if applicable)."""
        return self._session

    @asyncio.coroutine
    def get(self):
        """
        :ref:`coroutine<coroutine>` method.

        Get all messages from the stream.

        :returns: :py:class:`list` :py:class:`aiogremlin.subprotocol.Message`
        """
        return (yield from self._run())

    @asyncio.coroutine
    def _run(self):
        results = []
        while True:
            message = yield from self._stream.read()
            if message is None:
                break
            results.append(message)
        return results


class GremlinResponseStream:
    """
    Encapsulate and read Gremlin Server responses. Typically instantiated by
    GremlinResponse constructor, not by user.

    :param ``aiogremlin.response.GremlinClientWebSocketResponse`` ws: Websocket
        connection.
    :param loop: :ref:`event loop<asyncio-event-loop>` If param is ``None``,
        `asyncio.get_event_loop` is used for getting default event loop
        (optional)
    """
    def __init__(self, ws, username, password, loop=None):
        self._ws = ws
        self._username = username
        self._password = password
        self._loop = loop or asyncio.get_event_loop()
        data_stream = aiohttp.DataQueue(loop=self._loop)
        self._stream = self._ws.parser.set_parser(gremlin_response_parser,
                                                  output=data_stream)

    @asyncio.coroutine
    def read(self):
        """
        :ref:`coroutine<coroutine>` method

        Read a message from the stream.

        :returns: :py:class:`aiogremlin.subprotocol.Message`
        """
        if self._stream.at_eof():
            yield from self._ws.release()
            message = None
        else:
            asyncio.Task(self._ws.receive(), loop=self._loop)
            try:
                message = yield from self._stream.read()
                if message.status_code == 407:
                    writer = GremlinWriter(self._ws)
                    writer.write(op="authentication", username=self._username,
                                 password=self._password)
                    asyncio.Task(self._ws.receive(), loop=self._loop)
                    message = yield from self._stream.read()
            except (RequestError, GremlinServerError):
                yield from self._ws.release()
                raise
        return message


@asyncio.coroutine
def submit(gremlin, *,
           url='http://localhost:8182/',
           bindings=None,
           lang="gremlin-groovy",
           rebindings=None,
           op="eval",
           processor="",
           timeout=None,
           session=None,
           loop=None,
           conn_timeout=None,
           username="",
           password=""):
    """
    :ref:`coroutine<coroutine>`

    Submit a script to the Gremlin Server.

    :param str gremlin: The Gremlin script.
    :param str url: url for Gremlin Server (optional). 'http://localhost:8182/'
        by default
    :param dict bindings: A mapping of bindings for Gremlin script.
    :param str lang: Language of scripts submitted to the server.
        "gremlin-groovy" by default
    :param dict rebindings: Rebind ``Graph`` and ``TraversalSource``
        objects to different variable names in the current request
    :param str op: Gremlin Server op argument. "eval" by default.
    :param str processor: Gremlin Server processor argument. "" by default.
    :param float timeout: timeout for establishing connection (optional).
        Values ``0`` or ``None`` mean no timeout
    :param str session: Session id (optional). Typically a uuid
    :param loop: :ref:`event loop<asyncio-event-loop>` If param is ``None``,
        `asyncio.get_event_loop` is used for getting default event loop
        (optional)
    :param float conn_timeout: timeout for establishing connection (seconds)
        (optional). Values ``0`` or ``None`` mean no timeout
    :param username: Username for SASL auth
    :param password: Password for SASL auth
    :returns: :py:class:`aiogremlin.client.GremlinResponse` object
    """

    if loop is None:
        loop = asyncio.get_event_loop()

    connector = aiohttp.TCPConnector(force_close=True, loop=loop,
                                     verify_ssl=False,
                                     conn_timeout=conn_timeout)

    client_session = aiohttp.ClientSession(
        connector=connector, loop=loop,
        ws_response_class=GremlinClientWebSocketResponse)

    gremlin_client = GremlinClient(url=url, loop=loop,
                                   ws_connector=client_session,
                                   username=username, password=password)

    try:
        resp = yield from gremlin_client.submit(
            gremlin, bindings=bindings, lang=lang, rebindings=rebindings,
            op=op, processor=processor, session=session, timeout=timeout)

        return resp

    finally:
        gremlin_client.detach()
        client_session.detach()
