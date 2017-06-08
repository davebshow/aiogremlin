import json
import uuid

import pytest

from aiogremlin import driver
from gremlin_python.driver import request, serializer

@pytest.mark.asyncio
async def test_gremlin_query(event_loop, cluster):
    alias = { 'g': 'g' }
    cluster = await driver.Cluster.open(event_loop, aliases=alias)
    client = await cluster.connect()
    assert client.aliases == alias
    resp = await client.submit("1 + 1")
    async for msg in resp:
        print(msg)
    await cluster.close()


@pytest.mark.asyncio
async def test_alias_serialization(event_loop):
    alias = { 'g': 'g' }
    message = '1 + 1'
    cluster = await driver.Cluster.open(event_loop, aliases=alias)
    client = await cluster.connect()
    # This is the code client/conn uses on submit
    message = request.RequestMessage(
        processor='', op='eval',
        args={'gremlin': message,
              'aliases': client._aliases})
    request_id = str(uuid.uuid4())
    message = serializer.GraphSONMessageSerializer().serialize_message(
        request_id, message)
    message = message.decode('utf-8')[34:]
    aliases = json.loads(message)['args']['aliases']
    assert aliases == alias
    await cluster.close()
