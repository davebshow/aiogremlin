"""Client for the Tinkerpop 3 Gremlin Server."""

from aiogremlin import exception
from aiogremlin.gremlin_python.driver import request
from aiogremlin.gremlin_python.process import traversal


class Client:
    """
    Client that utilizes a :py:class:`Cluster<aiogremlin.cluster.Cluster>`
    to access a cluster of Gremlin Server hosts. Issues requests to hosts using
    a round robin strategy.

    :param aiogremlin.cluster.Cluster cluster: Cluster used by
        client
    :param asyncio.BaseEventLoop loop:
    :param dict aliases: Optional mapping for aliases. Default is `None`
    """
    def __init__(self, cluster, loop, *, aliases=None):
        self._cluster = cluster
        self._loop = loop
        if aliases is None:
            aliases = {}
        self._aliases = aliases

    @property
    def aliases(self):
        """Read-only property"""
        return self._aliases

    @property
    def message_serializer(self):
        """Read-only property"""
        return self.cluster.config['message_serializer']

    @property
    def cluster(self):
        """
        Read-only property.

        :returns: The instance of
            :py:class:`Cluster<aiogremlin.driver.cluster.Cluster>` associated with
            client.
        """
        return self._cluster

    async def close(self):
        await self._cluster.close()

    def alias(self, aliases):
        client = Client(self._cluster, self._loop,
                        aliases=aliases)
        return client

    async def submit(self, message, bindings=None):
        """
        **coroutine** Submit a script and bindings to the Gremlin Server.

        :param message: Can be an instance of
            `Message<aiogremlin.gremlin_python.request.RequestMessage>` or
            `Bytecode<aiogremlin.gremlin_python.process.traversal.Bytecode>`
            or a `str` representing a raw Gremlin script
        :param dict bindings: Optional bindings used with raw Grelmin
        :returns: :py:class:`ResultSet<aiogremlin.driver.resultset.ResultSet>`
            object
        """
        if isinstance(message, traversal.Bytecode):
            message = request.RequestMessage(
                processor='traversal', op='bytecode',
                args={'gremlin': message,
                      'aliases': self._aliases})
        elif isinstance(message, str):
            message = request.RequestMessage(
                processor='', op='eval',
                args={'gremlin': message,
                      'aliases': self._aliases})
            if bindings:
                message.args.update({'bindings': bindings})
        conn = await self.cluster.get_connection()
        resp = await conn.write(message)
        self._loop.create_task(conn.release_task(resp))
        return resp
