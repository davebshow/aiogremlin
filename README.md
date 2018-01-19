# [aiogremlin](https://pypi.python.org/pypi/aiogremlin/3.2.4)

[Official Documentation](http://aiogremlin.readthedocs.org/en/latest/)

`aiogremlin` is an asynchronous DSL based on the official `Gremlin-Python` GLV designed for integration with
event loop based asynchronous Python networking libraries, including `asyncio`,
`aiohttp`, and `tornado`. It uses the `async/await` syntax introduced
in PEP 492, and is therefore Python 3.5+ only.

`aiogremlin` tries to follow `Gremlin-Python` as closely as possible both in terms
of API and implementation. It is released according to the TinkerPop release schedule.

Note that this *NOT* an official Apache project component, it is a
*THIRD PARTY PACKAGE!*

## Getting Started

```python
import asyncio
from aiogremlin import DriverRemoteConnection, Graph


loop = asyncio.get_event_loop()


async def go(loop):
  remote_connection = await DriverRemoteConnection.open(
    'ws://localhost:8182/gremlin', 'g')
  g = Graph().traversal().withRemote(remote_connection)
  vertices = await g.V().toList()
  await remote_connection.close()
  return vertices


vertices = loop.run_until_complete(go(loop))
print(vertices)
# [v[1], v[2], v[3], v[4], v[5], v[6]]
```
