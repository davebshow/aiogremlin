import asyncio
from abc import ABCMeta, abstractmethod


class AbstractBaseFactory(metaclass=ABCMeta):

    @classmethod
    @abstractmethod
    def connect(cls):
        pass

    @property
    def factory(self):
        return self


class AbstractBaseConnection(metaclass=ABCMeta):

    def __init__(self, socket, pool=None):
        self.socket = socket
        self._pool = pool

    def feed_pool(self):
        if self.pool:
            if self in self.pool.active_conns:
                self.pool.feed_pool(self)

    @asyncio.coroutine
    def release(self):
        yield from self.close()
        if self in self.pool.active_conns:
            self.pool.active_conns.discard(self)

    @property
    def pool(self):
        return self._pool

    @property
    @abstractmethod
    def closed(self):
        pass

    @abstractmethod
    def close():
        pass

    @abstractmethod
    def send(self):
        pass

    @abstractmethod
    def recv(self):
        pass
