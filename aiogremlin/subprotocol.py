"""Implements the Gremlin Server subprotocol."""

import asyncio
import collections
import uuid

try:
    import ujson as json
except ImportError:
    import json

from aiogremlin.exceptions import RequestError, GremlinServerError
from aiogremlin.log import logger

__all__ = ("GremlinWriter",)


Message = collections.namedtuple(
    "Message",
    ["status_code", "data", "message", "metadata"])


def gremlin_response_parser(out, buf):
    while True:
        message = yield
        message = json.loads(message)
        message = Message(message["status"]["code"],
                          message["result"]["data"],
                          message["result"]["meta"],
                          message["status"]["message"])
        if message.status_code == 200:
            out.feed_data(message)
            out.feed_eof()
        elif message.status_code == 206:
            out.feed_data(message)
        elif message.status_code == 204:
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

    def write(self, gremlin, bindings=None, lang="gremlin-groovy", op="eval",
              processor="", session=None, binary=True,
              mime_type="application/json"):
        message = self._prepare_message(
            gremlin,
            bindings=bindings,
            lang=lang,
            op=op,
            processor=processor,
            session=session)
        message = json.dumps(message)
        if binary:
            message = self._set_message_header(message, mime_type)
        self._connection.send(message, binary)
        return self._connection

    @staticmethod
    def _set_message_header(message, mime_type):
        if mime_type == "application/json":
            mime_len = b"\x10"
            mime_type = b"application/json"
        else:
            raise ValueError("Unknown mime type.")
        return b"".join([mime_len, mime_type, bytes(message, "utf-8")])

    @staticmethod
    def _prepare_message(gremlin, bindings=None, lang="gremlin-groovy",
                         op="eval", processor="", session=None):
        message = {
            "requestId": str(uuid.uuid4()),
            "op": op,
            "processor": processor,
            "args": {
                "gremlin": gremlin,
                "bindings": bindings,
                "language":  lang
            }
        }
        if processor == "session":
            session = session or str(uuid.uuid4())
            message["args"]["session"] = session
            logger.info(
                "Session ID: {}".format(message["args"]["session"]))
        return message
