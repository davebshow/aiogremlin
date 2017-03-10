import asyncio
import functools

from aiogremlin import exception


def error_handler(fn):
    @functools.wraps(fn)
    async def wrapper(self):
        msg = await fn(self)
        if msg:
            if msg.status_code not in [200, 206]:
                self.close()
                raise exception.GremlinServerError(
                    msg.status_code,
                    "{0}: {1}".format(msg.status_code, msg.message))
            msg = msg.data
        return msg
    return wrapper


class ResultSet:
    """Gremlin Server response implementated as an async iterator."""
    def __init__(self, request_id, timeout, loop):
        self._response_queue = asyncio.Queue(loop=loop)
        self._request_id = request_id
        self._loop = loop
        self._timeout = timeout
        self._done = asyncio.Event(loop=self._loop)
        self._aggregate_to = None

    @property
    def request_id(self):
        return self._request_id

    @property
    def stream(self):
        return self._response_queue

    def queue_result(self, result):
        if result is None:
            self.close()
        self._response_queue.put_nowait(result)

    @property
    def done(self):
        """
        Readonly property.

        :returns: `asyncio.Event` object
        """
        return self._done

    @property
    def aggregate_to(self):
        return self._aggregate_to

    @aggregate_to.setter
    def aggregate_to(self, val):
        self._aggregate_to = val

    async def __aiter__(self):
        return self

    async def __anext__(self):
        msg = await self.one()
        if not msg:
            raise StopAsyncIteration
        return msg

    def close(self):
        self.done.set()
        self._loop = None

    @error_handler
    async def one(self):
        """Get a single message from the response stream"""
        if not self._response_queue.empty():
            msg = self._response_queue.get_nowait()
        elif self.done.is_set():
            msg = None
        else:
            try:
                msg = await asyncio.wait_for(self._response_queue.get(),
                                             timeout=self._timeout,
                                             loop=self._loop)
            except asyncio.TimeoutError:
                self.close()
                raise exception.ResponseTimeoutError('Response timed out')
        return msg

    async def all(self):
        results = []
        async for result in self:
            results.append(result)
        return results
