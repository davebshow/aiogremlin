from gremlin_python.driver.remote_connection import RemoteStrategy


class AsyncRemoteStrategy(RemoteStrategy):

    async def apply(self, traversal):
        if traversal.traversers is None:
            remote_traversal = await self.remote_connection.submit(
                traversal.bytecode)
            traversal.remote_results = remote_traversal
            traversal.side_effects = remote_traversal.side_effects
            traversal.traversers = remote_traversal.traversers
