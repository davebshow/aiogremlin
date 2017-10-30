'''
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
'''
'''THIS FILE HAS BEEN MODIFIED BY DAVID M. BROWN TO SUPPORT PEP 492'''
import pytest

from gremlin_python import statics
from gremlin_python.statics import long
from gremlin_python.process.traversal import Traverser
from gremlin_python.process.traversal import TraversalStrategy
from gremlin_python.process.graph_traversal import __
from aiogremlin.structure.graph import Graph
from gremlin_python.structure.graph import Vertex
from gremlin_python.process.strategies import SubgraphStrategy

__author__ = 'Marko A. Rodriguez (http://markorodriguez.com)'


class TestDriverRemoteConnection(object):

    @pytest.mark.asyncio
    async def test_label(self, remote_connection):
        statics.load_statics(globals())
        g = Graph().traversal().withRemote(remote_connection)
        result = await g.V().limit(1).toList()

    @pytest.mark.asyncio
    async def test_traversals(self, remote_connection):
        statics.load_statics(globals())
        g = Graph().traversal().withRemote(remote_connection)
        result = await g.V().count().toList()
        assert long(6) == result[0]
        # #
        assert Vertex(1) == await g.V(1).next()
        assert 1 == await g.V(1).id().next()
        assert Traverser(Vertex(1)) == await g.V(1).nextTraverser()
        result = await g.V(1).toList()
        assert 1 == len(result)
        result = await g.V(1).toList()
        assert isinstance(result, list)
        results = g.V().repeat(out()).times(2).name
        results = await results.toList()
        assert 2 == len(results)
        assert "lop" in results
        assert "ripple" in results
        # # #
        assert 10 == await g.V().repeat(both()).times(5)[0:10].count().next()
        assert 1 == await g.V().repeat(both()).times(5)[0:1].count().next()
        assert 0 == await g.V().repeat(both()).times(5)[0:0].count().next()
        assert 4 == await g.V()[2:].count().next()
        assert 2 == await g.V()[:2].count().next()
        # # #
        results = await g.withSideEffect('a',['josh','peter']).V(1).out('created').in_('created').values('name').where(within('a')).toList()
        assert 2 == len(results)
        assert 'josh' in results
        assert 'peter' in results
        # # # todo: need a traversal metrics deserializer
        # g.V().out().profile().next()
        await remote_connection.close()

    @pytest.mark.asyncio
    async def test_strategies(self, remote_connection):
        statics.load_statics(globals())
        #
        g = Graph().traversal().withRemote(remote_connection). \
            withStrategies(TraversalStrategy("SubgraphStrategy",
                                             {"vertices": __.hasLabel("person"),
                                              "edges": __.hasLabel("created")}))
        assert 4 == await g.V().count().next()
        assert 0 == await g.E().count().next()
        assert 1 == await g.V().label().dedup().count().next()
        assert "person" == await g.V().label().dedup().next()
        #
        g = Graph().traversal().withRemote(remote_connection). \
            withStrategies(SubgraphStrategy(vertices=__.hasLabel("person"), edges=__.hasLabel("created")))
        assert 4 == await g.V().count().next()
        assert 0 == await g.E().count().next()
        assert 1 == await g.V().label().dedup().count().next()
        assert "person" == await g.V().label().dedup().next()
        #
        g = g.withoutStrategies(SubgraphStrategy). \
            withComputer(vertices=__.has("name", "marko"), edges=__.limit(0))
        assert 1 == await g.V().count().next()
        assert 0 == await g.E().count().next()
        assert "person" == await g.V().label().next()
        assert "marko" == await g.V().name.next()
        #
        g = Graph().traversal().withRemote(remote_connection).withComputer()
        assert 6 == await g.V().count().next()
        assert 6 == await g.E().count().next()
        await remote_connection.close()

    @pytest.mark.asyncio
    async def test_side_effects(self, remote_connection):
        statics.load_statics(globals())
        g = Graph().traversal().withRemote(remote_connection)
        t = await g.V().hasLabel("project").name.iterate()
        keys = await t.side_effects.keys()
        assert 0 == len(keys)
        with pytest.raises(Exception):
            m = await t.side_effects["m"]
        t = g.V().out("created").groupCount("m").by("name")
        results = await t.toSet()
        assert 2 == len(results)
        assert Vertex(3) in results
        assert Vertex(5) in results
        keys = await t.side_effects.keys()
        assert 1 == len(keys)
        assert "m" in keys
        m = await t.side_effects["m"]
        assert isinstance(m, dict)
        assert 2 == len(m)
        assert 3 == m["lop"]
        assert 1 == m["ripple"]
        assert isinstance(m["lop"], long)
        assert isinstance(m["ripple"], long)
        # ##
        t = g.V().out("created").groupCount("m").by("name").name.aggregate("n")
        results = await t.toSet()
        assert 2 == len(results)
        assert "lop" in results
        assert "ripple" in results
        keys = await t.side_effects.keys()
        assert 2 == len(keys)
        assert "m" in keys
        assert "n" in keys
        n = await t.side_effects.get("n")
        assert isinstance(n, dict)
        assert 2 == len(n)
        assert "lop" in n.keys()
        assert "ripple" in n.keys()
        assert 3 == n["lop"]
        assert 1 == n["ripple"]
        #
        t = g.withSideEffect('m', 32).V().map(lambda: "x: x.sideEffects('m')")
        results = await t.toSet()
        assert 1 == len(results)
        assert 32 == list(results)[0]
        assert 32 == await t.side_effects['m']
        keys = await t.side_effects.keys()
        assert 1 == len(keys)
        with pytest.raises(Exception):
            x = await t.side_effects["x"]
        await remote_connection.close()

    @pytest.mark.asyncio
    async def test_side_effect_close(self, remote_connection):
        g = Graph().traversal().withRemote(remote_connection)
        t = g.V().aggregate('a').aggregate('b')
        await t.iterate()

        # The 'a' key should return some side effects
        results = await t.side_effects.get('a')
        assert results

        # Close result is None
        results = await t.side_effects.close()
        assert not results

        # Shouldn't get any new info from server
        # 'b' isn't in local cache
        results = await t.side_effects.get('b')
        assert not results

        # But 'a' should still be cached locally
        results = await t.side_effects.get('a')
        assert results

        # 'a' should have been added to local keys cache, but not 'b'
        results = await t.side_effects.keys()
        assert len(results) == 1
        a, = results
        assert a == 'a'

        # Try to get 'b' directly from server, should throw error
        with pytest.raises(Exception):
            await t.side_effects._get('b')
        await remote_connection.close()
