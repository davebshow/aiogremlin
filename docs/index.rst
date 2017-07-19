.. aiogremlin documentation master file, created by
   sphinx-quickstart on Sat Jun 27 13:50:06 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

==========
aiogremlin
==========

`aiogremlin` is a port of the official `Gremlin-Python` designed for integration with
event loop based asynchronous Python networking libraries, including `asyncio`_,
`aiohttp`_, and `tornado`_. It uses the `async/await` syntax introduced
in `PEP 492`_, and is therefore Python 3.5+ only.

`aiogremlin` tries to follow `Gremlin-Python` as closely as possible both in terms
of API and implementation. It is regularly rebased against the official Apache Git
repository, and will be released according to the `TinkerPop`_ release schedule.

Note that this *NOT* an official Apache project component, it is a
*THIRD PARTY PACKAGE!*

Releases
========
The latest release of :py:mod:`aiogremlin` is **3.2.5**.


Requirements
============

- Python 3.5+
- TinkerPop 3.2.5


Dependencies
============
- aiohttp 1.3.3
- PyYAML 3.12



Installation
============
Install using pip::

    $ pip install aiogremlin

For this version, a separate install of gremlinpython is required::

    $ pip install gremlinpython --no-deps


Getting Started
===============

:py:mod:`aiogremlin` has a simple API that is quite easy to use. However, as it relies
heavily on `asyncio`_ and `aiohttp`_, it is helpful to be familiar with the
basics of these modules.

:py:mod:`aiogremlin` is *very* similar to Gremlin-Python, except it is all async, all the time.

Minimal Example
---------------
Submit a script to the Gremlin Server::

    >>> import asyncio
    >>> from aiogremlin import DriverRemoteConnection, Graph

    >>> loop = asyncio.get_event_loop()

    >>> async def go(loop):
    ...    remote_connection = await DriverRemoteConnection.open(
    ...        'ws://localhost:8182/gremlin', 'g')
    ...    g = Graph().traversal().withRemote(remote_connection)
    ...    vertices = await g.V().toList()
    ...    return vertices

    >>> results = loop.run_until_complete(go(loop))
    >>> results
    # [v[1], v[2], v[3], v[4], v[5], v[6]]


The above example demonstrates how :py:mod:`aiogremlin` uses the
:ref:`event loop<asyncio-event-loop>` to drive communication with the Gremlin
Server, but the **rest of examples are written as if they were run in a Python
interpreter**. In reality, **this isn't possible**, so remember, code *must*
be wrapped in a coroutine and run with the :ref:`event loop<asyncio-event-loop>`.

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

.. _TinkerPop: http://tinkerpop.apache.org/
.. _`asyncio`: https://docs.python.org/3/library/asyncio.html
.. _`aiohttp`: http://aiohttp.readthedocs.org/en/latest/
.. _`Tornado`: http://www.tornadoweb.org/en/stable/
.. _`PEP 492`: https://www.python.org/dev/peps/pep-0492/
.. _Github: https://github.com/davebshow/aiogremlin/issues
