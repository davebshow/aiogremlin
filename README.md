# aiogremlin 0.0.1 [(gizmo grew up)](https://pypi.python.org/pypi/gizmo/0.1.12)

`aiogremlin` is a **Python 3** driver for the the [Tinkerpop 3 Gremlin Server](http://www.tinkerpop.com/docs/3.0.0.M7/#gremlin-server). This module is built on [Asyncio](https://docs.python.org/3/library/asyncio.html). By default it uses the [aiohttp](http://aiohttp.readthedocs.org/en/v0.15.3/index.html) socket client implementation, but it is easy to plug in a different implementation. `aiogremlin` is currently in **alpha** mode, but all major functionality has test coverage.

## Getting started

Since Python 3.4 is not the default version on many systems, it's nice to create a virtualenv that uses Python 3.4 by default. Then use pip to install `aiogremlin`. Using virtualenvwrapper on Ubuntu 14.04:

```bash
$ mkvirtualenv -p /usr/bin/python3.4 aiogremlin
$ pip install aiogremlin
```

Fire up the Gremlin Server:

```bash
$ ./bin/gremlin-server.sh
```

The `AsyncGremlinClient` communicates asynchronously with the Gremlin Server using websockets. The client uses a combination of [asyncio.coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutines) and  [asyncio.Task](https://docs.python.org/3/library/asyncio-task.html#task) run on Asyncio's pluggable event loop to achieve this communication.

The majority of ``AsyncGremlinClient`` methods are an `asyncio.coroutine`, so you will also need to use either `asyncio` or the `aiogremlin` [Task API](#task-api). The following examples use `asyncio` to demonstrate the use of the AsyncioGremlineClient.

The Gremlin Server sends responses in chunks, so `AsyncGremlinClient.submit` returns a list of gremlin response objects:

```python
>>> import asyncio
>>> loop = asyncio.get_event_loop()
>>> gc = GremlinClient('ws://localhost:8182/', loop=loop)
>>> submit = gc.submit("x + x", bindings={"x": 4})
>>> result = loop.run_until_complete(submit)
>>> result
[[8]]
>>> resp = result[0]
>>> resp.status_code
200
>>> resp
[8]
>>> loop.run_until_complete(gc.close())
>>> loop.close()
```
