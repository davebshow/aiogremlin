"""Implements the Gremlin Server subprotocol."""

import base64
import collections
import uuid

try:
    import ujson as json
except ImportError:
    import json

from aiogremlin.exceptions import RequestError, GremlinServerError

__all__ = ("GremlinWriter", "gremlin_response_parser", "Message")


Message = collections.namedtuple(
    "Message",
    ["status_code", "data", "message", "metadata"])


def gremlin_response_parser(out, buf):
    while True:
        message = yield
        message = json.loads(message)
        message = Message(message["status"]["code"],
                          message["result"]["data"],
                          message["status"]["message"],
                          message["result"]["meta"])
        if message.status_code == 200:
            out.feed_data(message)
            out.feed_eof()
        elif message.status_code == 206 or message.status_code == 407:
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

    def __init__(self, ws):
        self.ws = ws

    def write(self, *, gremlin="", bindings=None, lang="gremlin-groovy",
              rebindings=None, op="eval", processor="", session=None,
              binary=True, mime_type="application/json", username="",
              password=""):
        if rebindings is None:
            rebindings = {}
        if op == "eval":
            message = self._prepare_message(gremlin,
                                            bindings,
                                            lang,
                                            rebindings,
                                            op,
                                            processor,
                                            session)

        if op == "authentication":
            message = self._authenticate(
                username, password, session, processor)
        message = json.dumps(message)
        if binary:
            message = self._set_message_header(message, mime_type)
        self.ws.send(message, binary=binary)
        return self.ws

    @staticmethod
    def _set_message_header(message, mime_type):
        if mime_type == "application/json":
            mime_len = b"\x10"
            mime_type = b"application/json"
        else:
            raise ValueError("Unknown mime type.")
        return b"".join([mime_len, mime_type, bytes(message, "utf-8")])

    @staticmethod
    def _prepare_message(gremlin, bindings, lang, rebindings, op, processor,
                         session):
        message = {
            "requestId": str(uuid.uuid4()),
            "op": op,
            "processor": processor,
            "args": {
                "gremlin": gremlin,
                "bindings": bindings,
                "language":  lang,
                "rebindings": rebindings
            }
        }
        if session is None:
            if processor == "session":
                raise RuntimeError("session processor requires a session id")
        else:
            message["args"].update({"session": session})
        return message


    @staticmethod
    def _authenticate(username, password, session, processor):
        auth = b"".join([b"\x00", bytes(username, "utf-8"), b"\x00", bytes(password, "utf-8")])
        message = {
            "requestId": str(uuid.uuid4()),
            "op": "authentication",
            "processor": processor,
            "args": {
                "sasl": base64.b64encode(auth).decode()
            }
        }
        if session is None:
            if processor == "session":
                raise RuntimeError("session processor requires a session id")
        else:
            message["args"].update({"session": session})
        return message
