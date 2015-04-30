"""
"""

import asyncio
import itertools
import unittest
from aiogremlin import (GremlinClient, RequestError, GremlinServerError,
    SocketClientError, WebsocketPool, AiohttpFactory)


class GremlinClientTests(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        self.gc = GremlinClient("ws://localhost:8182/",
            factory=AiohttpFactory, loop=self.loop)

    def tearDown(self):
        self.loop.run_until_complete(self.gc.close())
        self.loop.close()

    def test_connection(self):
        @asyncio.coroutine
        def conn_coro():
            conn = yield from self.gc.connect()
            self.assertFalse(conn.closed)
            return conn
        conn = self.loop.run_until_complete(conn_coro())
        # Clean up the resource.
        self.loop.run_until_complete(conn.close())

    def test_sub(self):
        execute = self.gc.execute("x + x", bindings={"x": 4})
        results = self.loop.run_until_complete(execute)
        self.assertEqual(results[0].data[0], 8)

    def test_sub_waitfor(self):
        sub1 = self.gc.execute("x + x", bindings={"x": 1})
        sub2 = self.gc.execute("x + x", bindings={"x": 2})
        sub3 = self.gc.execute("x + x", bindings={"x": 4})
        coro = asyncio.wait([asyncio.async(sub1, loop=self.loop),
                             asyncio.async(sub2, loop=self.loop),
                             asyncio.async(sub3, loop=self.loop)], loop=self.loop)
        # Here I am looking for resource warnings.
        results = self.loop.run_until_complete(coro)
        self.assertIsNotNone(results)

    def test_resp_stream(self):
        @asyncio.coroutine
        def stream_coro():
            results = []
            resp = yield from self.gc.submit("x + x", bindings={"x": 4})
            while True:
                f = yield from resp.stream.read()
                if f is None:
                    break
                results.append(f)
            self.assertEqual(results[0].data[0], 8)
        self.loop.run_until_complete(stream_coro())

    def test_resp_get(self):
        @asyncio.coroutine
        def get_coro():
            conn = yield from self.gc.submit("x + x", bindings={"x": 4})
            results = yield from conn.get()
            self.assertEqual(results[0].data[0], 8)
        self.loop.run_until_complete(get_coro())

    def test_execute_error(self):
        execute = self.gc.execute("x + x g.asdfas", bindings={"x": 4})
        try:
            self.loop.run_until_complete(execute)
            error = False
        except:
            error = True
        self.assertTrue(error)


class WebsocketPoolTests(unittest.TestCase):

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
