"""Implements a very simple "protocol" for the Gremlin server."""

import asyncio
import collections

import ujson

from aiogremlin.exceptions import RequestError, GremlinServerError


Message = collections.namedtuple("Message", ["status_code", "data", "message",
    "metadata"])


def gremlin_response_parser(out, buf):
    while True:
        message = yield
        message = ujson.loads(message)
        message = Message(message["status"]["code"],
                          message["result"]["data"],
                          message["result"]["meta"],
                          message["status"]["message"])
        if message.status_code == 200:
            out.feed_data(message)
        elif message.status_code == 299:
            out.feed_data(message)
            out.feed_eof()
        else:
            if message.status_code < 500:
                raise RequestError(message.status_code, message.message)
            else:
                raise GremlinServerError(message.status_code, message.message)


class GremlinWriter:

    def __init__(self, connection):
        self._connection = connection

    @asyncio.coroutine
    def write(self, message, binary=True, mime_type="application/json"):
        message = ujson.dumps(message)
        if binary:
            message = self._set_message_header(message, mime_type)
        yield from self._connection.send(message, binary)
        return self._connection

    @staticmethod
    def _set_message_header(message, mime_type):
        if mime_type == "application/json":
            mime_len = b"\x10"
            mime_type = b"application/json"
        else:
            raise ValueError("Unknown mime type.")
        return b"".join([mime_len, mime_type, bytes(message, "utf-8")])
