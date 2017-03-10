from aiogremlin.gremlin_python.driver import request
from aiogremlin.gremlin_python.process import traversal



class RemoteTraversalSideEffects(traversal.TraversalSideEffects):
    def __init__(self, side_effect, client):
        self._side_effect = side_effect
        self._client = client
        self._keys = set()
        self._side_effects = {}
        self._closed = False

    async def __getitem__(self, key):
        if isinstance(key, slice):
            raise TypeError(
                'RemoteTraversalSideEffects does not support slicing')
        return await self.get(key)

    async def keys(self):
        """Get side effect keys associated with Traversal"""
        if not self._closed:
            message = request.RequestMessage(
                'traversal', 'keys',
                {'sideEffect': self._side_effect,
                'aliases': self._client.aliases})
            result_set = await self._client.submit(message)
            results = await result_set.all()
            self._keys = set(results)
        return self._keys

    async def get(self, key):
        """Get side effects associated with a specific key"""
        if not self._side_effects.get(key):
            if not self._closed:
                results = await self._get(key)
                self._side_effects[key] = results
                self._keys.add(key)
            else:
                return None
        return self._side_effects[key]

    async def _get(self, key):
        message = request.RequestMessage(
            'traversal', 'gather',
            {'sideEffect': self._side_effect, 'sideEffectKey': key,
             'aliases': self._client.aliases})
        result_set = await self._client.submit(message)
        return await self._aggregate_results(result_set)

    async def close(self):
        """Release side effects"""
        if not self._closed:
            message = request.RequestMessage(
                'traversal', 'close',
                {'sideEffect': self._side_effect,
                 'aliases': {'g': self._client.aliases}})
            result_set = await self._client.submit(message)
        self._closed = True
        return await result_set.one()

    async def _aggregate_results(self, result_set):
        aggregates = {'list': [], 'set': set(), 'map': {}, 'bulkset': {},
                      'none': None}
        results = None
        async for msg in result_set:
            if results is None:
                aggregate_to = result_set.aggregate_to
                results = aggregates.get(aggregate_to, [])
            # on first message, get the right result data structure
            # if there is no update to a structure, then the item is the result
            if results is None:
                results = msg
            # updating a map is different than a list or a set
            elif isinstance(results, dict):
                if aggregate_to == "map":
                    results.update(msg)
                else:
                    results[msg.object] = msg.bulk
            elif isinstance(results, set):
                results.update(msg)
            # flat add list to result list
            else:
                results.append(msg)
        if results is None:
            results = []
        return results
