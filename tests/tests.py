"""
"""

import asyncio
import itertools
import unittest
import uuid

import aiohttp
from aiogremlin import (GremlinClient, RequestError, GremlinServerError,
                        SocketClientError, WebSocketPool, GremlinFactory,
                        create_client, GremlinWriter, GremlinResponse,
                        GremlinClientWebSocketResponse)


class GremlinClientTests(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        self.gc = GremlinClient("ws://localhost:8182/", loop=self.loop)

    def tearDown(self):
        self.loop.run_until_complete(self.gc.close())
        self.loop.close()

    def test_connection(self):
        @asyncio.coroutine
        def conn_coro():
            conn = yield from self.gc._acquire()
            self.assertFalse(conn.closed)
            return conn
        conn = self.loop.run_until_complete(conn_coro())
        # Clean up the resource.
        self.loop.run_until_complete(conn.close())

    def test_sub(self):
        @asyncio.coroutine
        def go():
            resp = yield from self.gc.execute("x + x", bindings={"x": 4})
            return resp
        results = self.loop.run_until_complete(go())
        self.assertEqual(results[0].data[0], 8)


class GremlinClientPoolTests(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        pool = WebSocketPool("ws://localhost:8182/", loop=self.loop)
        self.gc = GremlinClient(url="ws://localhost:8182/",
                                factory=GremlinFactory(loop=self.loop),
                                pool=pool,
                                loop=self.loop)

    def tearDown(self):
        self.loop.run_until_complete(self.gc.close())
        self.loop.close()

    def test_connection(self):
        @asyncio.coroutine
        def conn_coro():
            conn = yield from self.gc._acquire()
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
        coro = asyncio.gather(*[asyncio.async(sub1, loop=self.loop),
                              asyncio.async(sub2, loop=self.loop),
                              asyncio.async(sub3, loop=self.loop)],
                              loop=self.loop)
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

    def test_session_gen(self):
        execute = self.gc.execute("x + x", processor="session",
                                  bindings={"x": 4})
        results = self.loop.run_until_complete(execute)
        self.assertEqual(results[0].data[0], 8)

    def test_session(self):
        @asyncio.coroutine
        def stream_coro():
            session = str(uuid.uuid4())
            resp = yield from self.gc.submit("x + x", bindings={"x": 4},
                                             session=session)
            while True:
                f = yield from resp.stream.read()
                if f is None:
                    break
            self.assertEqual(resp.session, session)
        self.loop.run_until_complete(stream_coro())


class WebSocketPoolTests(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        self.pool = WebSocketPool("ws://localhost:8182/",
                                  poolsize=2,
                                  timeout=1,
                                  loop=self.loop,
                                  factory=GremlinFactory(loop=self.loop))

    def tearDown(self):
        self.loop.run_until_complete(self.pool.close())
        self.loop.close()

    def test_connect(self):

        @asyncio.coroutine
        def conn():
            conn = yield from self.pool.acquire()
            self.assertFalse(conn.closed)
            self.pool.release(conn)
            self.assertEqual(self.pool.num_active_conns, 0)

        self.loop.run_until_complete(conn())

    def test_multi_connect(self):

        @asyncio.coroutine
        def conn():
            conn1 = yield from self.pool.acquire()
            conn2 = yield from self.pool.acquire()
            self.assertFalse(conn1.closed)
            self.assertFalse(conn2.closed)
            self.pool.release(conn1)
            self.assertEqual(self.pool.num_active_conns, 1)
            self.pool.release(conn2)
            self.assertEqual(self.pool.num_active_conns, 0)

        self.loop.run_until_complete(conn())

    def test_timeout(self):

        @asyncio.coroutine
        def conn():
            conn1 = yield from self.pool.acquire()
            conn2 = yield from self.pool.acquire()
            try:
                conn3 = yield from self.pool.acquire()
                timeout = False
            except asyncio.TimeoutError:
                timeout = True
            self.assertTrue(timeout)

        self.loop.run_until_complete(conn())

    def test_socket_reuse(self):

        @asyncio.coroutine
        def conn():
            conn1 = yield from self.pool.acquire()
            conn2 = yield from self.pool.acquire()
            try:
                conn3 = yield from self.pool.acquire()
                timeout = False
            except asyncio.TimeoutError:
                timeout = True
            self.assertTrue(timeout)
            self.pool.release(conn2)
            conn3 = yield from self.pool.acquire()
            self.assertFalse(conn1.closed)
            self.assertFalse(conn3.closed)
            self.assertEqual(conn2, conn3)

        self.loop.run_until_complete(conn())

    def test_socket_repare(self):

        @asyncio.coroutine
        def conn():
            conn1 = yield from self.pool.acquire()
            conn2 = yield from self.pool.acquire()
            self.assertFalse(conn1.closed)
            self.assertFalse(conn2.closed)
            yield from conn1.close()
            yield from conn2.close()
            self.assertTrue(conn2.closed)
            self.assertTrue(conn2.closed)
            self.pool.release(conn1)
            self.pool.release(conn2)
            conn1 = yield from self.pool.acquire()
            conn2 = yield from self.pool.acquire()
            self.assertFalse(conn1.closed)
            self.assertFalse(conn2.closed)

        self.loop.run_until_complete(conn())


class ContextMngrTest(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        self.pool = WebSocketPool("ws://localhost:8182/",
                                  poolsize=1,
                                  loop=self.loop,
                                  factory=GremlinFactory(loop=self.loop),
                                  max_retries=0)

    def tearDown(self):
        self.loop.run_until_complete(self.pool.close())
        self.loop.close()

    @asyncio.coroutine
    def _check_closed(self):
        conn = self.pool._pool.get_nowait()
        self.assertTrue(conn.closed)
        writer = GremlinWriter(conn)
        try:
            conn = yield from writer.write("1 + 1")
            error = False
        except RuntimeError:
            error = True
        self.assertTrue(error)

    def test_connection_manager(self):
        results = []

        @asyncio.coroutine
        def go():
            with (yield from self.pool) as conn:
                writer = GremlinWriter(conn)
                conn = writer.write("1 + 1")
                resp = GremlinResponse(conn, pool=self.pool, loop=self.loop)
                while True:
                    mssg = yield from resp.stream.read()
                    if mssg is None:
                        break
                    results.append(mssg)
            # Test that connection was closed
            yield from self._check_closed()
        self.loop.run_until_complete(go())

    def test_connection_manager_with_client(self):
        @asyncio.coroutine
        def go():
            with (yield from self.pool) as conn:
                gc = GremlinClient(connection=conn, loop=self.loop)
                resp = yield from gc.submit("1 + 1")
                self.assertEqual(conn, resp.stream._conn)
                result = yield from resp.get()
                self.assertEqual(result[0].data[0], 2)

                self.pool.release(conn)
            # Test that connection was closed
            yield from self._check_closed()
        self.loop.run_until_complete(go())

    def test_connection_manager_with_client_closed_conn(self):
        @asyncio.coroutine
        def go():
            with (yield from self.pool) as conn:
                conn._closing = True
                conn._close()
                gc = GremlinClient(connection=conn, loop=self.loop)
                resp = yield from gc.submit("1 + 1")
                self.assertNotEqual(conn, resp.stream._conn)
                result = yield from resp.get()
                self.assertEqual(result[0].data[0], 2)
                yield from resp.stream._conn.close()
            # Test that connection was closed
        self.loop.run_until_complete(go())

    def test_connection_manager_error(self):
        results = []

        @asyncio.coroutine
        def go():
            with (yield from self.pool) as conn:
                writer = GremlinWriter(conn)
                conn = writer.write("1 + 1 sdalfj;sd")
                resp = GremlinResponse(conn, pool=self.pool, loop=self.loop)
                try:
                    while True:
                        mssg = yield from resp.stream.read()
                        if mssg is None:
                            break
                        results.append(mssg)
                except:
                    self.pool.release(conn)
                    raise
        try:
            self.loop.run_until_complete(go())
            err = False
        except:
            err = True
        self.assertTrue(err)
        self.loop.run_until_complete(self._check_closed())


class GremlinClientPoolSessionTests(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        pool = WebSocketPool(
            "ws://localhost:8182/",
            loop=self.loop,
            factory=aiohttp.ClientSession(
                loop=self.loop,
                ws_response_class=GremlinClientWebSocketResponse))
        self.gc = GremlinClient("ws://localhost:8182/",
                                pool=pool,
                                loop=self.loop)

    def tearDown(self):
        self.gc._pool._factory.close()
        self.loop.run_until_complete(self.gc.close())
        self.loop.close()

    def test_connection(self):
        @asyncio.coroutine
        def conn_coro():
            conn = yield from self.gc._acquire()
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
        coro = asyncio.gather(*[asyncio.async(sub1, loop=self.loop),
                              asyncio.async(sub2, loop=self.loop),
                              asyncio.async(sub3, loop=self.loop)],
                              loop=self.loop)
        # Here I am looking for resource warnings.
        results = self.loop.run_until_complete(coro)
        self.assertIsNotNone(results)


class CreateClientTests(unittest.TestCase):

    def test_pool_init(self):
        @asyncio.coroutine
        def go(loop):
            gc = yield from create_client(poolsize=10, loop=loop)
            self.assertEqual(gc._pool._pool.qsize(), 10)
            yield from gc.close()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        loop.run_until_complete(go(loop))
        loop.close()


if __name__ == "__main__":
    unittest.main()
