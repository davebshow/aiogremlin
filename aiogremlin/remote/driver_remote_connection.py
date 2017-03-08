import asyncio
from urllib.parse import urlparse

from aiogremlin.driver.cluster import Cluster
from aiogremlin.gremlin_python.driver import serializer
from aiogremlin.remote.driver_remote_side_effects import RemoteTraversalSideEffects
from aiogremlin.gremlin_python.driver.remote_connection import RemoteTraversal


__author__ = 'David M. Brown (davebshow@gmail.com)'


class DriverRemoteConnection:

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
    async def using(cls, cluster, aliases=None, *, loop=None):
        client = await cluster.connect(aliases=aliases)
        if not loop:
            loop = asyncio.get_event_loop()
        return cls(client, loop)

    @classmethod
    async def open(cls, url=None, aliases=None, loop=None, *,
                   graphson_reader=None, graphson_writer=None, **config):
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
        if self._cluster:
            await self._cluster.close()

    async def submit(self, bytecode):
        result_set = await self._client.submit(bytecode)
        side_effects = RemoteTraversalSideEffects(result_set.request_id,
                                                  self._client)
        return RemoteTraversal(result_set, side_effects)
