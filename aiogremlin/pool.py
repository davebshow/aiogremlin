import asyncio

from aiogremlin.connection import AiohttpFactory
from aiogremlin.contextmanager import ConnectionContextManager
from aiogremlin.log import logger


def create_pool():
    pass


class WebSocketPool:

    def __init__(self, uri='ws://localhost:8182/', factory=None, poolsize=10,
                 max_retries=10, timeout=None, loop=None, verbose=False):
        """
        """
        self.uri = uri
        self._factory = factory or AiohttpFactory
        self.poolsize = poolsize
        self.max_retries = max_retries
        self.timeout = timeout
        self._connected = False
        self._loop = loop or asyncio.get_event_loop()
        self._pool = asyncio.Queue(maxsize=self.poolsize, loop=self._loop)
        self.active_conns = set()
        self.num_connecting = 0
        self._closed = False
        if verbose:
            logger.setLevel(INFO)

    @asyncio.coroutine
    def fill_pool(self):
        for i in range(self.poolsize):
            conn = yield from self.factory.connect(self.uri, pool=self,
                loop=self._loop)
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
        while True:
            try:
                conn = self._pool.get_nowait()
            except asyncio.QueueEmpty:
                break
            else:
                yield from conn.close()

    @asyncio.coroutine
    def acquire(self, uri=None, loop=None, num_retries=None):
        if self._closed:
            raise RuntimeError("WebsocketPool is closed.")
        if num_retries is None:
            num_retries = self.max_retries
        uri = uri or self.uri
        loop = loop or self.loop
        if not self._pool.empty():
            socket = self._pool.get_nowait()
            logger.info("Reusing socket: {} at {}".format(socket, uri))
        elif self.num_active_conns + self.num_connecting >= self.poolsize:
            logger.info("Waiting for socket...")
            socket = yield from asyncio.wait_for(self._pool.get(),
                self.timeout, loop=loop)
            logger.info("Socket acquired: {} at {}".format(socket, uri))
        else:
            self.num_connecting += 1
            try:
                socket = yield from self.factory.connect(uri, pool=self,
                    loop=loop)
            finally:
                self.num_connecting -= 1
        if not socket.closed:
            logger.info("New connection on socket: {} at {}".format(
                socket, uri))
            self.active_conns.add(socket)
        # Untested.
        elif num_retries > 0:
            logger.warning("Got bad socket, retry...")
            socket = yield from self.acquire(uri, loop, num_retries - 1)
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
        return ConnectionContextManager(conn, self)
