.. aiogremlin documentation master file, created by
   sphinx-quickstart on Sat Jun 27 13:50:06 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

==========
aiogremlin
==========

:py:mod:`aiogremlin` is an asynchronous client for the `Tinkerpop 3 Gremlin Server`_
based on the `asyncio`_ and `aiohttp`_ libraries.

Releases
========
The latest release of :py:mod:`aiogremlin` is **0.1.0**.


Requirements
============

- Python 3.4
- Tinkerpop 3 Gremlin Server 3.0.0

Using Python 2? Checkout `gremlinrestclient`_.

Dependencies
============
- aiohttp 0.16.5
- aiowebsocketclient 0.0.3

To speed up serialization, you can also install `ujson`_. If not available,
aiogremlin will use the Python standard library :any:`json<json>` module.

- ujson 1.33


Installation
============
Install using pip::

    $ pip install aiogremlin


Getting Started
===============

:py:mod:`aiogremlin` has a simple API that is quite easy to use. However, as it relies
heavily on `asyncio`_ and `aiohttp`_, it is helpful to be familar with the
basics of these modules. If you're not, maybe check out the :py:mod:`asyncio`
documentation relating to the :ref:`event loop<asyncio-event-loop>` and the
concept of the :ref:`coroutine<coroutine>`. Also, I would recommend the
documentation relating to :py:mod:`aiohttp`'s
:ref:`websocket client<aiohttp-client-websockets>` and
:ref:`HTTP client<aiohttp-client-reference>` implementations.

Minimal Example
---------------
Submit a script to the Gremlin Server::

    >>> import asyncio
    >>> import aiogremlin
    >>> @asyncio.coroutine
    ... def go():
    ...     resp = yield from aiogremlin.submit("1 + 1")
    ...     return (yield from resp.get())
    >>> loop = asyncio.get_event_loop()
    >>> results = loop.run_until_complete(go())
    >>> results
    [Message(status_code=200, data=[2], message={}, metadata='')]


The above example demonstrates how :py:mod:`aiogremlin` uses the
:ref:`event loop<asyncio-event-loop>` to drive communication with the Gremlin
Server, but the **rest of examples are written as if they were run in a Python
interpreter**. In reality, **this isn't possible**, so remember, code *must*
be wrapped in functions and run with the :ref:`event loop<asyncio-event-loop>`.

Contribute
----------

Contributions are welcome. If you find a bug, or have a suggestion, please open
an issue on `Github`_. If you would like to make a pull request, please make
sure to add appropriate tests and run them::

    $ python setup.py test

In the future there will be CI and more info on contributing.

Contents:

.. toctree::
   :maxdepth: 3

   usage
   modules


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _Tinkerpop 3 Gremlin Server: http://tinkerpop.incubator.apache.org/
.. _`asyncio`: https://docs.python.org/3/library/asyncio.html
.. _`aiohttp`: http://aiohttp.readthedocs.org/en/latest/
.. _`ujson`: https://pypi.python.org/pypi/ujson
.. _Github: https://github.com/davebshow/aiogremlin/issues
.. _`gremlinrestclient`: http://gremlinrestclient.readthedocs.org/en/latest/
