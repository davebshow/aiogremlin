"""Abstract classes for creating pluggable websocket clients."""

from abc import ABCMeta, abstractmethod


class AbstractFactory(metaclass=ABCMeta):

    @classmethod
    @abstractmethod
    def connect(cls):
        pass

    @property
    @abstractmethod
    def factory(self):
        pass


class AbstractConnection(metaclass=ABCMeta):

    @abstractmethod
    def feed_pool(self):
        pass

    @abstractmethod
    def release(self):
        pass

    @property
    @abstractmethod
    def pool(self):
        pass

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
    def receive(self):
        pass

    @abstractmethod
    def _receive(self):
        pass
