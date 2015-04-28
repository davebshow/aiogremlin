"""
"""

import asyncio
import itertools
import websockets
import unittest
from aiogremlin import (GremlinClient, async, Group, Chain, Chord, RequestError,
    GremlinServerError, SocketClientError, WebsocketPool, AiohttpFactory)


class GremlinClientTests(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        self.gc = GremlinClient("ws://localhost:8182/",
            factory=AiohttpFactory, loop=self.loop)

    def tearDown(self):
        self.loop.run_until_complete(self.gc.close())
        self.loop.close()

    @asyncio.coroutine
    def consumer_coro1(self, x):
        yield from asyncio.sleep(0.25, loop=self.loop)
        return x[0] ** 0

    @asyncio.coroutine
    def consumer_coro2(self, x):
        yield from asyncio.sleep(0.5, loop=self.loop)
        return x[0] ** 1

    def test_connection(self):
        @asyncio.coroutine
        def conn_coro():
            conn = yield from self.gc.connect()
            self.assertFalse(conn.closed)

        self.loop.run_until_complete(conn_coro())

    def test_task(self):
        t = async(self.gc.submit, "x + x", bindings={"x": 2},
            consumer=lambda x : x, loop=self.loop)
        message = t.execute()
        self.assertEqual(4, message[0])

    def test_task_error(self):
        t = async(self.gc.submit, "x + x g.adasdfd", bindings={"x": 2},
            consumer=lambda x : x[0] ** 2, loop=self.loop)
        try:
            t.execute()
            error = False
        except:
            error = True
        self.assertTrue(error)

    def test_submittask(self):
        t = self.gc.s("x + x", bindings={"x": 2},
            consumer=lambda x : x[0] ** 2)
        t()
        message = t.get()
        self.assertEqual(16, message[0])

    def test_group(self):
        t = self.gc.s("x + x", bindings={"x": 2},
            consumer=lambda x : x[0] ** 2)
        slow = self.gc.s("x + x", bindings={"x": 2},
            consumer=self.consumer_coro1)
        g = Group(slow, t, loop=self.loop)
        results = g.execute()
        self.assertEqual(len(results), 2)
        results = list(itertools.chain.from_iterable(results))
        self.assertTrue(16 in results)
        self.assertTrue(1 in results)

    def test_group_error(self):
        t = self.gc.s("x + x g.sdfa", bindings={"x": 2},
            consumer=lambda x : x[0] ** 2)
        slow = self.gc.s("x + x", bindings={"x": 2},
            consumer=self.consumer_coro1)
        g = Group(slow, t, loop=self.loop)
        try:
            g.execute()
            error = False
        except:
            error = True
        self.assertTrue(error)

    def test_group_of_groups(self):
        fast = self.gc.s("x + x", bindings={"x": 2},
            consumer=lambda x : x[0] ** 2)
        fast1 = self.gc.s("x + x", bindings={"x": 2},
            consumer=lambda x : x[0] ** 2)
        slow = self.gc.s("x + x", bindings={"x": 2}, consumer=self.consumer_coro1)
        slow1 = self.gc.s("x + x", bindings={"x": 2}, consumer=self.consumer_coro1)
        g = Group(fast, fast1, loop=self.loop)
        g1 = Group(slow, slow1, loop=self.loop)
        results = Group(g, g1, loop=self.loop).execute()
        self.assertEqual(len(results), 2)
        self.assertEqual(len(results[0]), 2)
        self.assertEqual(len(results[1]), 2)
        results = list(itertools.chain.from_iterable(results))
        results = list(itertools.chain.from_iterable(results))
        self.assertTrue(1 in results)
        self.assertTrue(16 in results)
        results.remove(1)
        results.remove(16)
        self.assertTrue(1 in results)
        self.assertTrue(16 in results)

    def test_group_itrbl_arg(self):
        t = self.gc.s("x + x", bindings={"x": 2},
            consumer=lambda x : x[0] ** 2)
        slow = self.gc.s("x + x", bindings={"x": 2},
            consumer=self.consumer_coro1)
        g = Group([slow, t], loop=self.loop)
        results = g.execute()
        self.assertEqual(len(results), 2)
        results = list(itertools.chain.from_iterable(results))
        self.assertTrue(1 in results)
        self.assertTrue(16 in results)

    def test_chain(self):
        t = self.gc.s("x + x", bindings={"x": 2},
            consumer=lambda x : x[0] ** 2)
        slow = self.gc.s("x + x", bindings={"x": 2},
            consumer=self.consumer_coro1)
        results = Chain(slow, t, loop=self.loop).execute()
        self.assertEqual(results[0][0], 1)
        self.assertEqual(results[1][0], 16)

    def test_chain_error(self):
        t = self.gc.s("x + x g.sadf", bindings={"x": 2},
            consumer=lambda x : x[0] ** 2)
        slow = self.gc.s("x + x", bindings={"x": 2},
            consumer=self.consumer_coro1)
        try:
            Chain(slow, t, loop=self.loop).execute()
            error = False
        except:
            error = True
        self.assertTrue(error)

    def test_chains_in_group(self):
        slow = self.gc.s("x + x", bindings={"x": 2},
            consumer=self.consumer_coro2)
        slow1 = self.gc.s("x + x", bindings={"x": 2},
            consumer=self.consumer_coro1)
        slow_chain = Chain(slow, slow1, loop=self.loop)
        t = self.gc.s("x + x", bindings={"x": 2},
            consumer=lambda x : x[0] ** 2)
        results = Group(slow_chain, t, loop=self.loop).execute()
        self.assertEqual(slow_chain.result[0][0], 4)
        self.assertEqual(slow_chain.result[1][0], 1)
        self.assertEqual(t.result[0], 16)

    def test_chains_in_group_error(self):
        slow = self.gc.s("x + x g.edfsa", bindings={"x": 2},
            consumer=self.consumer_coro2)
        slow1 = self.gc.s("x + x g.eafwa", bindings={"x": 2},
            consumer=self.consumer_coro1)
        slow_chain = Chain(slow, slow1, loop=self.loop)

        t = self.gc.s("x + x", bindings={"x": 2},
            consumer=lambda x : x[0] ** 2)
        try:
            Group(slow_chain, t, loop=self.loop).execute()
            error = False
        except:
            error = True
        self.assertTrue(error)

    def test_chain_itrbl_arg(self):
        t = self.gc.s("x + x", bindings={"x": 2},
            consumer=lambda x : x[0] ** 2)
        slow = self.gc.s("x + x", bindings={"x": 2},
            consumer=self.consumer_coro1)
        results = Chain([slow, t], loop=self.loop).execute()
        self.assertEqual(results[0][0], 1)
        self.assertEqual(results[1][0], 16)

    def test_group_chain(self):
        results = []
        slow = self.gc.s("x + x", bindings={"x": 2}, consumer=self.consumer_coro1)
        slow1 = self.gc.s("x + x", bindings={"x": 2}, consumer=self.consumer_coro1)
        slow_group = Group(slow, slow1, loop=self.loop)
        fast = self.gc.s("x + x", bindings={"x": 2},
            consumer=lambda x : x[0] ** 2)
        fast1 = self.gc.s("x + x", bindings={"x": 2},
            consumer=lambda x : x[0] ** 2)
        fast_group = Group(fast, fast1, loop=self.loop)
        results = Chain(slow_group, fast_group, loop=self.loop).execute()
        self.assertEqual(results[0][0][0], 1)
        self.assertEqual(results[0][1][0], 1)
        self.assertEqual(results[1][0][0], 16)
        self.assertEqual(results[1][1][0], 16)

    def test_chord(self):
        slow1 = self.gc.s("x + x", bindings={"x": 2},
            consumer=self.consumer_coro1)
        slow2 = self.gc.s("x + x", bindings={"x": 2},
            consumer=self.consumer_coro2)
        t = self.gc.s("x + x", bindings={"x": 2},
            consumer=lambda x : x[0] ** 2)
        results = Chord([slow2, slow1], t, loop=self.loop).execute()
        flat = list(itertools.chain.from_iterable(results[0]))
        self.assertTrue(1 in flat)
        self.assertTrue(4 in flat)
        self.assertEqual(results[1][0], 16)

    def test_chord_group_error(self):
        slow1 = self.gc.s("x + x g.asdf", bindings={"x": 2},
            consumer=self.consumer_coro1)
        slow2 = self.gc.s("x + x", bindings={"x": 2},
            consumer=self.consumer_coro2)
        t = self.gc.s("x + x", bindings={"x": 2},
            consumer=lambda x : x[0] ** 2)
        try:
            Chord([slow2, slow1], t, loop=self.loop).execute()
            error = False
        except:
            error = True
        self.assertTrue(error)

    def test_z_e2e(self):
        t = self.gc.s("g.V().remove(); g.E().remove();", collect=False)
        t1 = self.gc.s("g.addVertex('uniqueId', x)", bindings={"x": "joe"},
            collect=False)
        t2 = self.gc.s("g.addVertex('uniqueId', x)", bindings={"x": "maria"},
            collect=False)
        t3 = self.gc.s("g.addVertex('uniqueId', x)", bindings={"x": "jill"},
            collect=False)
        t4 = self.gc.s("g.addVertex('uniqueId', x)", bindings={"x": "jack"},
            collect=False)
        g1 = Group(t1, t2, t3, t4, loop=self.loop)
        t5 = self.gc.s("""
            joe = g.V().has('uniqueId', 'joe').next();
            maria = g.V().has('uniqueId', 'maria').next();
            joe.addEdge('marriedTo', maria);""")
        t6 = self.gc.s("""
            jill = g.V().has('uniqueId', 'jill').next();
            jack = g.V().has('uniqueId', 'jack').next();
            jill.addEdge('marriedTo', jack);""")
        t7 = self.gc.s("""
            jill = g.V().has('uniqueId', 'jill').next();
            joe = g.V().has('uniqueId', 'joe').next();
            jill.addEdge('hasSibling', joe);""")
        g2 = Group(t5, t6, t7, loop=self.loop)
        t8 = self.gc.s("g.V();", consumer=lambda x: print(x))
        t9 = self.gc.s("g.E();", consumer=lambda x: print(x))
        t10 = self.gc.s("g.V().count();", consumer=lambda x: self.assertEqual(x[0], 4))
        t11 = self.gc.s("g.E().count();", consumer=lambda x: self.assertEqual(x[0], 3))
        c = Chain(t, g1, g2, t8, t9, t10, t11, t, loop=self.loop)
        results = c.execute()
        print(results)

    def test_sub(self):
        @asyncio.coroutine
        def sub_coro():
            results = []
            results = yield from self.gc.submit("x + x", bindings={"x": 4})
            self.assertEqual(results[0][0], 8)

        self.loop.run_until_complete(sub_coro())

    def test_recv(self):
        @asyncio.coroutine
        def recv_coro():
            results = []
            websocket = yield from self.gc.send("x + x", bindings={"x": 4})
            while True:
                f = yield from self.gc.recv(websocket)
                if f is None:
                    break
                else:
                    results.append(f)
            self.assertEqual(results[0]["result"]["data"][0], 8)

        self.loop.run_until_complete(recv_coro())

    def test_submit_error(self):
        @asyncio.coroutine
        def submit_coro():
            yield from self.gc.submit("x + x g.asdfas", bindings={"x": 4})

        try:
            self.loop.run_until_complete(submit_coro())
            error = False
        except:
            error = True
        self.assertTrue(error)


class ConnectionManagerTests(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        self.pool = WebsocketPool(poolsize=2, timeout=1, loop=self.loop,
            factory=AiohttpFactory)

    def tearDown(self):
        self.loop.run_until_complete(self.pool.close())
        self.loop.close()

    def test_connect(self):

        @asyncio.coroutine
        def conn():
            conn = yield from self.pool.connect()
            self.assertIsNotNone(conn.socket)
            self.assertFalse(conn.closed)
            conn.feed_pool()
            self.assertEqual(self.pool.num_active_conns, 0)

        self.loop.run_until_complete(conn())

    def test_multi_connect(self):

        @asyncio.coroutine
        def conn():
            conn1 = yield from self.pool.connect()
            conn2 = yield from self.pool.connect()
            self.assertIsNotNone(conn1.socket)
            self.assertFalse(conn1.closed)
            self.assertIsNotNone(conn2.socket)
            self.assertFalse(conn2.closed)
            conn1.feed_pool()
            self.assertEqual(self.pool.num_active_conns, 1)
            conn2.feed_pool()
            self.assertEqual(self.pool.num_active_conns, 0)

        self.loop.run_until_complete(conn())

    def test_timeout(self):

        @asyncio.coroutine
        def conn():
            conn1 = yield from self.pool.connect()
            conn2 = yield from self.pool.connect()
            try:
                conn3 = yield from self.pool.connect()
                timeout = False
            except asyncio.TimeoutError:
                timeout = True
            self.assertTrue(timeout)

        self.loop.run_until_complete(conn())

    def test_socket_reuse(self):

        @asyncio.coroutine
        def conn():
            conn1 = yield from self.pool.connect()
            conn2 = yield from self.pool.connect()
            try:
                conn3 = yield from self.pool.connect()
                timeout = False
            except asyncio.TimeoutError:
                timeout = True
            self.assertTrue(timeout)
            conn2.feed_pool()
            conn3 = yield from self.pool.connect()
            self.assertIsNotNone(conn1.socket)
            self.assertFalse(conn1.closed)
            self.assertIsNotNone(conn3.socket)
            self.assertFalse(conn3.closed)
            self.assertEqual(conn2.socket, conn3.socket)

        self.loop.run_until_complete(conn())

    def test_socket_repare(self):

        @asyncio.coroutine
        def conn():
            conn1 = yield from self.pool.connect()
            conn2 = yield from self.pool.connect()
            self.assertIsNotNone(conn1.socket)
            self.assertFalse(conn1.closed)
            self.assertIsNotNone(conn2.socket)
            self.assertFalse(conn2.closed)
            # conn1.socket._closed = True
            # conn2.socket._closed = True
            yield from conn1.socket.close()
            yield from conn2.socket.close()
            self.assertTrue(conn2.closed)
            self.assertTrue(conn2.closed)
            conn1.feed_pool()
            conn2.feed_pool()
            conn1 = yield from self.pool.connect()
            conn2 = yield from self.pool.connect()
            self.assertIsNotNone(conn1.socket)
            self.assertFalse(conn1.closed)
            self.assertIsNotNone(conn2.socket)
            self.assertFalse(conn2.closed)

        self.loop.run_until_complete(conn())


if __name__ == "__main__":
    unittest.main()
