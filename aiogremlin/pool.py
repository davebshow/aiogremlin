import asyncio

from aiogremlin.connection import (GremlinFactory,
                                   GremlinClientWebSocketResponse)
from aiogremlin.contextmanager import ConnectionContextManager
from aiogremlin.log import logger

__all__ = ("WebSocketPool",)


class WebSocketPool:

    def __init__(self, url, *, factory=None, poolsize=10, connector=None,
                 max_retries=10, timeout=None, loop=None, verbose=False,
                 ws_response_class=None):
        """
        """
        self.url = url
        if ws_response_class is None:
            ws_response_class = GremlinClientWebSocketResponse
        self.poolsize = poolsize
        self.max_retries = max_retries
        self.timeout = timeout
        self._connected = False
        self._loop = loop or asyncio.get_event_loop()
        self._factory = factory or GremlinFactory(connector=connector,
                                                  loop=self._loop)
        self._pool = asyncio.Queue(maxsize=self.poolsize, loop=self._loop)
        self.active_conns = set()
        self.num_connecting = 0
        self._closed = False
        if verbose:
            logger.setLevel(INFO)

    @asyncio.coroutine
    def fill_pool(self):
        tasks = []
        poolsize = self.poolsize
        for i in range(poolsize):
            coro = self.factory.ws_connect(self.url)
            task = asyncio.async(coro, loop=self._loop)
            tasks.append(task)
        for f in asyncio.as_completed(tasks, loop=self._loop):
            conn = yield from f
            self._put(conn)
        self._connected = True

    @property
    def loop(self):
        return self._loop

    @property
    def factory(self):
        return self._factory

    @property
    def closed(self):
        return self._closed

    @property
    def num_active_conns(self):
        return len(self.active_conns)

    def release(self, conn):
        if self._closed:
            raise RuntimeError("WebsocketPool is closed.")
        self.active_conns.discard(conn)
        self._put(conn)

    @asyncio.coroutine
    def close(self):
        try:
            self._factory.close()
        except AttributeError:
            pass
        if not self._closed:
            if self.active_conns:
                yield from self._close_active_conns()
            yield from self._purge_pool()
            self._closed = True

    @asyncio.coroutine
    def _close_active_conns(self):
        tasks = [asyncio.async(conn.close(), loop=self.loop) for conn
                 in self.active_conns]
        yield from asyncio.wait(tasks, loop=self.loop)

    @asyncio.coroutine
    def _purge_pool(self):
        while not self._pool.empty():
            conn = self._pool.get_nowait()
            yield from conn.close()

    @asyncio.coroutine
    def acquire(self, url=None, loop=None, num_retries=None):
        if self._closed:
            raise RuntimeError("WebsocketPool is closed.")
        if num_retries is None:
            num_retries = self.max_retries
        url = url or self.url
        loop = loop or self.loop
        if not self._pool.empty():
            socket = self._pool.get_nowait()
            logger.info("Reusing socket: {} at {}".format(socket, url))
        elif self.num_active_conns + self.num_connecting >= self.poolsize:
            logger.info("Waiting for socket...")
            socket = yield from asyncio.wait_for(self._pool.get(),
                                                 self.timeout, loop=loop)
            logger.info("Socket acquired: {} at {}".format(socket, url))
        else:
            self.num_connecting += 1
            try:
                socket = yield from self.factory.ws_connect(url)
            finally:
                self.num_connecting -= 1
        if not socket.closed:
            logger.info("New connection on socket: {} at {}".format(
                        socket, url))
            self.active_conns.add(socket)
        # Untested.
        elif num_retries > 0:
            logger.warning("Got bad socket, retry...")
            socket = yield from self.acquire(url, loop, num_retries - 1)
        else:
            raise RuntimeError("Unable to connect, max retries exceeded.")
        return socket

    def _put(self, socket):
        try:
            self._pool.put_nowait(socket)
        except asyncio.QueueFull:
            pass
            # This should be - not working
            # yield from socket.release()

    # aioredis style
    def __enter__(self):
        raise RuntimeError(
            "'yield from' should be used as a context manager expression")

    def __exit__(self, *args):
        pass

    def __iter__(self):
        conn = yield from self.acquire()
        return ConnectionContextManager(conn)
