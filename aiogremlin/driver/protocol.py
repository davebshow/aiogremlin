import asyncio
import base64
import collections
import logging

try:
    import ujson as json
except ImportError:
    import json

from gremlin_python.driver import protocol, request, serializer


__author__ = 'David M. Brown (davebshow@gmail.com)'


logger = logging.getLogger(__name__)


Message = collections.namedtuple(
    "Message",
    ["status_code", "data", "message"])


class GremlinServerWSProtocol(protocol.AbstractBaseProtocol):
    """Implemenation of the Gremlin Server Websocket protocol"""
    def __init__(self, message_serializer, username='', password=''):
        if isinstance(message_serializer, type):
            message_serializer = message_serializer()
        self._message_serializer = message_serializer
        self._username = username
        self._password = password

    def connection_made(self, transport):
        self._transport = transport

    async def write(self, request_id, request_message):
        message = self._message_serializer.serialize_message(
            request_id, request_message)
        func = self._transport.write(message)
        if asyncio.iscoroutine(func):
            await func

    async def data_received(self, data, results_dict):
        serializer_version = self._message_serializer.version
        data = data.decode('utf-8')
        message = json.loads(data)
        request_id = message['requestId']
        status_code = message['status']['code']
        data = message['result']['data']
        msg = message['status']['message']
        if request_id in results_dict:
            result_set = results_dict[request_id]
            if serializer_version == b"application/vnd.gremlin-v2.0+json":
                aggregate_to = data['result']['meta'].get('aggregateTo', 'list')
            else:
                meta_aggregate_to = message['result']['meta']['@value']
                if len(meta_aggregate_to) > 1:
                    aggregate_to = meta_aggregate_to[1]
                else:
                    aggregate_to = 'list'
            result_set.aggregate_to = aggregate_to

            if status_code == 407:
                auth = b''.join([b'\x00', self._username.encode('utf-8'),
                                 b'\x00', self._password.encode('utf-8')])
                request_message = request.RequestMessage(
                    'traversal', 'authentication',
                    {'sasl': base64.b64encode(auth).decode()})
                await self.write(request_id, request_message)
            elif status_code == 204:
                result_set.queue_result(None)
            else:
                if data:
                    if serializer_version == b"application/vnd.gremlin-v2.0+json":
                        for result in data:
                            result = self._message_serializer.deserialize_message(result)
                            message = Message(status_code, result, msg)
                            result_set.queue_result(message)
                    else:
                        results = self._message_serializer.deserialize_message(data['@value'])
                        for result in results:
                            message = Message(status_code, result, msg)
                            result_set.queue_result(message)
                else:
                    data = self._message_serializer.deserialize_message(data)
                    message = Message(status_code, data, msg)
                    result_set.queue_result(message)
                if status_code != 206:
                    result_set.queue_result(None)
