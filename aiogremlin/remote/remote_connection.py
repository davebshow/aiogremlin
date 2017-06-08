from gremlin_python.process import traversal


class AsyncRemoteStrategy(traversal.TraversalStrategy):
    def __init__(self, remote_connection):
        self.remote_connection = remote_connection

    async def apply(self, traversal):
        if traversal.traversers is None:
            remote_traversal = await self.remote_connection.submit(
                traversal.bytecode)
            traversal.remote_results = remote_traversal
            traversal.side_effects = remote_traversal.side_effects
            traversal.traversers = remote_traversal.traversers
