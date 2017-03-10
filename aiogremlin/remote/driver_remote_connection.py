import asyncio
from urllib.parse import urlparse

from aiogremlin.driver.cluster import Cluster
from aiogremlin.gremlin_python.driver import serializer
from aiogremlin.remote.driver_remote_side_effects import RemoteTraversalSideEffects
from aiogremlin.gremlin_python.driver.remote_connection import RemoteTraversal


__author__ = 'David M. Brown (davebshow@gmail.com)'


class DriverRemoteConnection:
    """
    Remote connection to a Gremlin Server. Do not instantiate directly,
    instead use :py:meth:`DriverRemoteConnection.open` or
    :py:meth:`DriverRemoteConnection.using`

    :param aiogremlin.driver.client.Client client:
    :param asyncio.BaseEventLoop loop:
    :param aiogremlin.driver.cluster.Cluster cluster:
    """

    def __init__(self, client, loop, *, cluster=None):
        self._client = client
        self._loop = loop
        self._cluster = cluster

    @property
    def client(self):
        return self._client

    @property
    def config(self):
        return self._cluster.config

    @classmethod
    async def using(cls, cluster, aliases=None):
        """
        Create a :py:class:`DriverRemoteConnection` using a specific
        :py:class:`Cluster<aiogremlin.driver.cluster.Cluster>`

        :param aiogremlin.driver.cluster.Cluster cluster:
        :param dict aliases: Optional mapping for aliases. Default is `None`.
            Also accepts `str` argument which will be assigned to `g`
        """
        client = await cluster.connect(aliases=aliases)
        loop = cluster._loop
        return cls(client, loop)

    @classmethod
    async def open(cls, url=None, aliases=None, loop=None, *,
                   graphson_reader=None, graphson_writer=None, **config):
        """
        :param str url: Optional url for host Gremlin Server

        :param dict aliases: Optional mapping for aliases. Default is `None`.
            Also accepts `str` argument which will be assigned to `g`
        :param asyncio.BaseEventLoop loop:
        :param graphson_reader: Custom graphson_reader
        :param graphson_writer: Custom graphson_writer
        :param config: Optional cluster configuration passed as kwargs or `dict`
        """
        if url:
            parsed_url = urlparse(url)
            config.update({
                'scheme': parsed_url.scheme,
                'hosts': [parsed_url.hostname],
                'port': parsed_url.port})
        if isinstance(aliases, str):
            aliases = {'g': aliases}
        if not loop:
            loop = asyncio.get_event_loop()
        message_serializer = serializer.GraphSONMessageSerializer(
            reader=graphson_reader,
            writer=graphson_writer)
        config.update({'message_serializer': message_serializer})
        cluster = await Cluster.open(loop, aliases=aliases, **config)
        client = await cluster.connect()
        return cls(client, loop, cluster=cluster)

    async def close(self):
        """
        Close underlying cluster if applicable. If created with
        :py:meth:`DriverRemoteConnection.using`, cluster is NOT closed.
        """
        if self._cluster:
            await self._cluster.close()

    async def submit(self, bytecode):
        """Submit bytecode to the Gremlin Server"""
        result_set = await self._client.submit(bytecode)
        side_effects = RemoteTraversalSideEffects(result_set.request_id,
                                                  self._client)
        return RemoteTraversal(result_set, side_effects)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
        self._client = None
        self._cluster = None
