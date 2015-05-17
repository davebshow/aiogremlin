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

    @property
    @abstractmethod
    def closed(self):
        pass

    @abstractmethod
    def close():
        pass

    @abstractmethod
    def _close():
        pass

    @abstractmethod
    def send(self):
        pass

    @abstractmethod
    def receive(self):
        pass
