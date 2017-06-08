from gremlin_python.process import traversal


class RemoteStrategy(traversal.TraversalStrategy):
    def __init__(self, remote_connection):
        self.remote_connection = remote_connection

    async def apply(self, traversal):
        if traversal.traversers is None:
            remote_traversal = await self.remote_connection.submit(
                traversal.bytecode)
            traversal.remote_results = remote_traversal
            traversal.side_effects = remote_traversal.side_effects
            traversal.traversers = remote_traversal.traversers


class RemoteTraversal(traversal.Traversal):
    def __init__(self, traversers, side_effects):
        super(RemoteTraversal, self).__init__(None, None, None)
        self.traversers = traversers
        self._side_effects = side_effects

    @property
    def side_effects(self):
        return self._side_effects

    @side_effects.setter
    def side_effects(self, val):
        self._side_effects = val
