"""
"""

import asyncio
import unittest
import uuid
import aiohttp
from aiogremlin import (submit, GremlinConnector, GremlinClient,
                        GremlinClientSession, GremlinServerError,
                        GremlinClientWebSocketResponse)
from tests import SubmitTest, GremlinClientTest, GremlinClientSessionTest


class SaslSubmitTest(SubmitTest):

    def setUp(self):
        self.uri = 'https://localhost:8182/'
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)


class SaslGremlinClientTest(GremlinClientTest):

    def setUp(self):
        self.uri = 'https://localhost:8182/'
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        connector = aiohttp.TCPConnector(force_close=False, loop=self.loop,
                                         verify_ssl=False)

        client_session = aiohttp.ClientSession(
            connector=connector, loop=self.loop,
            ws_response_class=GremlinClientWebSocketResponse)

        self.gc = GremlinClient(url=self.uri, loop=self.loop,
                                username="stephen", password="password",
                                client_session=client_session)


class SaslGremlinClientSessionTest(GremlinClientSessionTest):

    def setUp(self):
        self.uri = 'https://localhost:8182/'
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        connector = aiohttp.TCPConnector(force_close=False, loop=self.loop,
                                         verify_ssl=False)

        client_session = aiohttp.ClientSession(
            connector=connector, loop=self.loop,
            ws_response_class=GremlinClientWebSocketResponse)

        self.gc = GremlinClientSession(url=self.uri,
                                       loop=self.loop,
                                       username="stephen", password="password",
                                       client_session=client_session)

        self.script1 = """v=graph.addVertex('name', 'Dave')"""

        self.script2 = "v.property('name')"


if __name__ == "__main__":
    unittest.main()
