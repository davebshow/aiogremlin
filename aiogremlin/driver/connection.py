import abc
import asyncio
import base64
import collections
import logging
import uuid

import aiohttp

try:
    import ujson as json
except ImportError:
    import json

from aiogremlin.driver import provider, resultset
from aiogremlin.driver.protocol import GremlinServerWSProtocol
from aiogremlin.driver.aiohttp.transport import AiohttpTransport
from aiogremlin.gremlin_python.driver import serializer


logger = logging.getLogger(__name__)


class Connection:
    """
    Main classd for interacting with the Gremlin Server. Encapsulates a
    websocket connection. Not instantiated directly. Instead use
    :py:meth:`Connection.open<aiogremlin.connection.Connection.open>`.

    :param str url: url for host Gremlin Server
    :param aiogremlin.gremlin_python.driver.transport.AbstractBaseTransport transport:
        Transport implementation
    :param aiogremlin.gremlin_python.driver.protocol.AbstractBaseProtocol protocol:
        Protocol implementation
    :param asyncio.BaseEventLoop loop:
    :param str username: Username for database auth
    :param str password: Password for database auth
    :param int max_inflight: Maximum number of unprocessed requests at any
        one time on the connection
    :param float response_timeout: (optional) `None` by default
    """
    def __init__(self, url, transport, protocol, loop, username, password,
                 max_inflight, response_timeout, message_serializer, provider):
        self._url = url
        self._transport = transport
        self._protocol = protocol
        self._loop = loop
        self._response_timeout = response_timeout
        self._username = username
        self._password = password
        self._closed = False
        self._result_sets = {}
        self._receive_task = self._loop.create_task(self._receive())
        self._semaphore = asyncio.Semaphore(value=max_inflight,
                                            loop=self._loop)
        if isinstance(message_serializer, type):
            message_serializer = message_serializer()
        self._message_serializer = message_serializer
        self._provider = provider

    @classmethod
    async def open(cls, url, loop, *,
                   protocol=None,
                   transport_factory=None,
                   ssl_context=None,
                   username='',
                   password='',
                   max_inflight=64,
                   response_timeout=None,
                   message_serializer=serializer.GraphSONMessageSerializer,
                   provider=provider.TinkerGraph):
        """
        **coroutine** Open a connection to the Gremlin Server.

        :param str url: url for host Gremlin Server
        :param asyncio.BaseEventLoop loop:
        :param aiogremlin.gremlin_python.driver.protocol.AbstractBaseProtocol protocol:
            Protocol implementation
        :param func transport_factory: Factory function for transports
        :param ssl.SSLContext ssl_context:
        :param str username: Username for database auth
        :param str password: Password for database auth

        :param int max_inflight: Maximum number of unprocessed requests at any
            one time on the connection
        :param float response_timeout: (optional) `None` by default
        :param message_serializer: Message serializer implementation
        :param provider: Graph provider object implementation

        :returns: :py:class:`Connection<aiogremlin.connection.Connection>`
        """
        if not protocol:
            protocol = GremlinServerWSProtocol(message_serializer)
        if not transport_factory:
            transport_factory = lambda: AiohttpTransport(loop)
        transport = transport_factory()
        await transport.connect(url, ssl_context=ssl_context)
        return cls(url, transport, protocol, loop, username, password,
                   max_inflight, response_timeout, message_serializer,
                   provider)

    @property
    def message_serializer(self):
        return self._message_serializer

    @property
    def closed(self):
        """
        Read-only property. Check if connection has been closed.

        :returns: `bool`
        """
        return self._closed or self._transport.closed

    @property
    def url(self):
        """
        Readonly property.

        :returns: str The url association with this connection.
        """
        return self._url

    async def write(self, message):
        """
        Submit a script and bindings to the Gremlin Server

        :param `RequestMessage<aiogremlin.gremlin_python.driver.request.RequestMessage>` message:
        :returns: :py:class:`ResultSet<aiogremlin.driver.resultset.ResultSet>`
            object
        """
        await self._semaphore.acquire()
        request_id = str(uuid.uuid4())
        message = self._message_serializer.serialize_message(
            request_id, message)
        if self._transport.closed:
            await self._transport.connect(self.url)
        self._transport.write(message)
        result_set = resultset.ResultSet(request_id, self._response_timeout,
                                   self._loop)
        self._result_sets[request_id] = result_set
        self._loop.create_task(
            self._terminate_response(result_set, request_id))
        return result_set

    submit = write

    async def close(self):
        """**coroutine** Close underlying connection and mark as closed."""
        self._receive_task.cancel()
        await self._transport.close()
        self._closed = True

    async def _terminate_response(self, resp, request_id):
        await resp.done.wait()
        del self._result_sets[request_id]
        self._semaphore.release()

    async def _receive(self):
        while True:
            data = await self._transport.read()
            await self._protocol.data_received(data, self._result_sets)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
        self._transport = None
