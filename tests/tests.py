"""
"""

import asyncio
import unittest
import uuid
import aiohttp
from aiogremlin import (submit, GremlinConnector, GremlinClient,
                        GremlinClientSession, GremlinServerError,
                        GremlinClientWebSocketResponse)


class SubmitTest(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)

    def tearDown(self):
        self.loop.close()

    def test_submit(self):

        @asyncio.coroutine
        def go():
            resp = yield from submit("x + x", url='http://localhost:8182/',
                                     bindings={"x": 4}, loop=self.loop,
                                     username="stephen", password="password")
            results = yield from resp.get()
            return results
        results = self.loop.run_until_complete(go())
        self.assertEqual(results[0].data[0], 8)

    def test_rebinding(self):

        @asyncio.coroutine
        def go1():
            result = yield from submit("graph2.addVertex()",
                                       url='http://localhost:8182/',
                                       loop=self.loop, username="stephen",
                                       password="password")
            resp = yield from result.get()

        try:
            self.loop.run_until_complete(go1())
            error = False
        except GremlinServerError:
            error = True
        self.assertTrue(error)

        @asyncio.coroutine
        def go2():
            result = yield from submit(
                "graph2.addVertex()", url='http://localhost:8182/',
                rebindings={"graph2": "graph"}, loop=self.loop,
                username="stephen", password="password")
            resp = yield from result.get()
            self.assertEqual(len(resp), 1)

        try:
            self.loop.run_until_complete(go2())
        except GremlinServerError:
            print("RELEASE DOES NOT SUPPORT REBINDINGS")


class GremlinClientTest(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)

        self.gc = GremlinClient(url="http://localhost:8182/", loop=self.loop)

    def tearDown(self):
        self.loop.run_until_complete(self.gc.close())
        self.loop.close()

    def test_connection(self):

        @asyncio.coroutine
        def go():
            ws = yield from self.gc._connector.ws_connect(self.gc.url)
            self.assertFalse(ws.closed)
            yield from ws.close()

        self.loop.run_until_complete(go())

    def test_execute(self):

        @asyncio.coroutine
        def go():
            resp = yield from self.gc.execute("x + x", bindings={"x": 4})
            return resp

        results = self.loop.run_until_complete(go())
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

    def test_execute_error(self):
        execute = self.gc.execute("x + x g.asdfas", bindings={"x": 4})
        try:
            self.loop.run_until_complete(execute)
            error = False
        except:
            error = True
        self.assertTrue(error)

    def test_rebinding(self):
        execute = self.gc.execute("graph2.addVertex()")
        try:
            self.loop.run_until_complete(execute)
            error = False
        except GremlinServerError:
            error = True
        self.assertTrue(error)

        @asyncio.coroutine
        def go():
            result = yield from self.gc.execute(
                "graph2.addVertex()", rebindings={"graph2": "graph"})
            self.assertEqual(len(result), 1)

        try:
            self.loop.run_until_complete(go())
        except GremlinServerError:
            print("RELEASE DOES NOT SUPPORT REBINDINGS")


class GremlinClientSessionTest(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        self.gc = GremlinClientSession(url="http://localhost:8182/",
                                       loop=self.loop)

        self.script1 = """v=graph.addVertex('name', 'Dave')"""

        self.script2 = "v.property('name')"

    def tearDown(self):
        self.loop.run_until_complete(self.gc.close())
        self.loop.close()

    def test_session(self):

        @asyncio.coroutine
        def go():
            yield from self.gc.execute(self.script1)
            results = yield from self.gc.execute(self.script2)
            return results

        results = self.loop.run_until_complete(go())
        self.assertEqual(results[0].data[0]['value'], 'Dave')

    def test_session_reset(self):

        @asyncio.coroutine
        def go():
            yield from self.gc.execute(self.script1)
            self.gc.reset_session()
            results = yield from self.gc.execute(self.script2)
            return results
        try:
            results = self.loop.run_until_complete(go())
            error = False
        except GremlinServerError:
            error = True
        self.assertTrue(error)

    def test_session_manual_reset(self):

        @asyncio.coroutine
        def go():
            yield from self.gc.execute(self.script1)
            new_sess = str(uuid.uuid4())
            sess = self.gc.reset_session(session=new_sess)
            self.assertEqual(sess, new_sess)
            self.assertEqual(self.gc.session, new_sess)
            results = yield from self.gc.execute(self.script2)
            return results
        try:
            results = self.loop.run_until_complete(go())
            error = False
        except GremlinServerError:
            error = True
        self.assertTrue(error)

    def test_session_set(self):

        @asyncio.coroutine
        def go():
            yield from self.gc.execute(self.script1)
            new_sess = str(uuid.uuid4())
            self.gc.session = new_sess
            self.assertEqual(self.gc.session, new_sess)
            results = yield from self.gc.execute(self.script2)
            return results
        try:
            results = self.loop.run_until_complete(go())
            error = False
        except GremlinServerError:
            error = True
        self.assertTrue(error)

    def test_resp_session(self):

        @asyncio.coroutine
        def go():
            session = str(uuid.uuid4())
            self.gc.session = session
            resp = yield from self.gc.submit("x + x", bindings={"x": 4})
            while True:
                f = yield from resp.stream.read()
                if f is None:
                    break
            self.assertEqual(resp.session, session)

        self.loop.run_until_complete(go())


if __name__ == "__main__":
    unittest.main()
