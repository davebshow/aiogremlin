from aiogremlin.process import graph_traversal
from aiogremlin.process.traversal import AsyncTraversalStrategies

from gremlin_python.structure import graph


class Graph(graph.Graph):

    def __init__(self):
        if self.__class__ not in AsyncTraversalStrategies.global_cache:
            AsyncTraversalStrategies.global_cache[
                self.__class__] = AsyncTraversalStrategies()

    def traversal(self, traversal_source_class=None):
        if not traversal_source_class:
            traversal_source_class = graph_traversal.AsyncGraphTraversalSource
        return traversal_source_class(
            self, AsyncTraversalStrategies.global_cache[self.__class__])
