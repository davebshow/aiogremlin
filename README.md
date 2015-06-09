# aiogremlin 0.0.9 [(gizmo grew up)](https://pypi.python.org/pypi/gizmo/0.1.12)

`aiogremlin` is a **Python 3** driver for the the [Tinkerpop 3 Gremlin Server](http://tinkerpop.incubator.apache.org/docs/3.0.0.M9-incubating/#gremlin-server). This module is built on [Asyncio](https://docs.python.org/3/library/asyncio.html) and [aiohttp](http://aiohttp.readthedocs.org/en/v0.15.3/index.html) `aiogremlin` is currently in **alpha** mode, but all major functionality has test coverage.


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

The `GremlinClient` communicates asynchronously with the Gremlin Server using websockets. The majority of `GremlinClient` methods are an `asyncio.coroutine`, so you will also need to use `asyncio`:

```python
>>> import asyncio
>>> from aiogremlin import GremlinClient
```

The Gremlin Server responds with messages in chunks, `GremlinClient.submit` submits a script to the server, and returns a `GremlinResponse` object. This object provides the methods: `get` and the property `stream`. `get` collects all of the response messages and returns them as a Python list. `stream` returns an object of the type `GremlinResponseStream` that implements a method `read`. This allows you to read the response without loading all of the messages into memory.

Note that the GremlinClient constructor and the create_client function take [keyword only arguments](https://www.python.org/dev/peps/pep-3102/) only!


```python
>>> loop = asyncio.get_event_loop()
>>> gc = GremlinClient(url='ws://localhost:8182/', loop=loop)  # Default url
# Or even better, use the constructor function. This will init pool connections.
# ***Must be done inside a coroutine***
>>> gc = yield from create_client(loop=loop)
# Or outside of a coroutine using the loop to help
>>> gc = loop.run_until_complete(create_client(loop=loop))

# Use get.
>>> @asyncio.coroutine
... def get(gc):
...     resp = yield from gc.submit("x + x", bindings={"x": 4})
...     result = yield from resp.get()
...     return result

>>> result = loop.run_until_complete(get(gc))
>>> result
[Message(status_code=200, data=[8], message={}, metadata='')]

>>> resp = result[0]
>>> resp.status_code
200

>>> resp  # Named tuple.
Message(status_code=200, data=[8], message={}, metadata='')

# Use stream.
>>> @asyncio.coroutine
... def stream(gc):
...     resp = yield from gc.submit("x + x", bindings={"x": 1})
...     while True:
...         result = yield from resp.stream.read()
...         if result is None:
...             break
...         print(result)
>>> loop.run_until_complete(stream(gc))
Message(status_code=200, data=[2], message={}, metadata='')

>>> loop.run_until_complete(gc.close())  # Explicitly close client!!!
>>> loop.close()
```

For convenience, `aiogremlin` also provides a method `execute`, which is equivalent to calling  `yield from submit()` and then `yield from get()` in the same coroutine.

```python
>>> loop = asyncio.get_event_loop()
>>> gc = GremlinClient(loop=loop)
>>> execute = gc.execute("x + x", bindings={"x": 4})
>>> result = loop.run_until_complete(execute)
>>> result
[Message(status_code=200, data=[8], message={}, metadata='')]
>>> loop.run_until_complete(gc.close())  # Explicitly close client!!!
>>> loop.close()
```

To avoid the explicit client close, `aiogremlin` provides a class called `ConnectionContextManager`. To create an instance of `ConnectionContextManager`, get a connection from a `WebSocketPool` instance as follows:

```python
>>> loop = asyncio.get_event_loop()
# Note that url is a required positional param here!
# Pool does not open any connections until requested.
>>> pool = aiogremlin.WebSocketPool('ws://localhost:8182/')
>>> @asyncio.coroutine
... def go(pool, loop):
...     with (yield from pool) as conn:
...         gc = aiogremlin.GremlinClient(connection=conn, loop=loop)
...         resp = yield from gc.execute("1 + 1")
...     return resp
>>> result = loop.run_until_complete(go(pool, loop))
>>> result
[Message(status_code=200, data=[2], message={}, metadata='')]
>>> loop.close()  # Close loop, but client connections will be closed.
```
