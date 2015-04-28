"""
Implements a very simple "protocol" for the Gremlin server.
"""
import asyncio
import json

from .exceptions import RequestError, GremlinServerError


@asyncio.coroutine
def gremlin_response_parser(connection):
    message = yield from connection.recv()
    message = json.loads(message)
    status_code = message["status"]["code"]
    if status_code == 200:
        return message
    elif status_code == 299:
        connection.feed_pool()
        # Return None
    else:
        try:
            message = message["status"]["message"]
            if status_code < 500:
                raise RequestError(status_code, message)
            else:
                raise GremlinServerError(status_code, message)
        finally:
            yield from connection.release()


class GremlinWriter:

    def __init__(self, connection):
        self._connection = connection

    @asyncio.coroutine
    def send(self, message, binary=True, mime_type="application/json"):
        if binary:
            message = self._set_message_header(message, mime_type)
        yield from self._connection.send(message, binary)

    @staticmethod
    def _set_message_header(message, mime_type):
        if mime_type == "application/json":
            mime_len = b"\x10"
            mime_type = b"application/json"
        else:
            raise ValueError("Unknown mime type.")
        return b"".join([mime_len, mime_type, bytes(message, "utf-8")])
