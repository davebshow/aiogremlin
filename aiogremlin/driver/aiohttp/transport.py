import aiohttp

from aiogremlin.gremlin_python.driver import transport


class AiohttpTransport(transport.AbstractBaseTransport):

    def __init__(self, loop):
        self._loop = loop
        self._connected = False

    async def connect(self, url, *, ssl_context=None):
        await self.close()
        connector = aiohttp.TCPConnector(
            ssl_context=ssl_context, loop=self._loop)
        self._client_session = aiohttp.ClientSession(
            loop=self._loop, connector=connector)
        self._ws = await self._client_session.ws_connect(url)
        self._connected = True

    def write(self, message):
        self._ws.send_bytes(message)

    async def read(self):
        return await self._ws.receive()

    async def close(self):
        if self._connected:
            if not self._ws.closed:
                await self._ws.close()
            if not self._client_session.closed:
                await self._client_session.close()

    @property
    def closed(self):
        return self._ws.closed or self._client_session.closed
