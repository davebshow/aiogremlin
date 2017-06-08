import asyncio

from gremlin_python.process import traversal


class AsyncTraversalStrategies(traversal.TraversalStrategies):

    async def apply_strategies(self, traversal):
        for traversal_strategy in self.traversal_strategies:
            func = traversal_strategy.apply(traversal)
            if asyncio.iscoroutine(func):
                await func
