Using aiogremlin
================

Before you get started, make sure you have the `Gremlin Server`_ up and running.
All of the following example assume a running Gremlin Server version 3.0.0.M9 at
'ws://localhost:8182/'.


Submitting a script with :py:func:`submit`
------------------------------------------


The simplest way to interact with the Gremlin Server is by using the
:py:func:`aiogremlin.client.submit` function::

    >>> resp = yield from aiogremlin.submit("x + x", bindings={"x": 2})

This returns an instance of :py:class:`aiogremlin.client.GremlinResponse`. This
class provides the interface used to read the underlying response stream. The
easiest way to read the stream is using the
:py:meth:`aiogremlin.client.GremlinResponse.get`::

    >>> results = yield from resp.get()

However, if you are expecting a huge result set from the server, you may want to
read the chunked responses one at a time::

    >>> results = []
    >>> while True:
    ...     msg = yield from resp.stream.read():
    ...     if msg is None:
    ...         break
    ...     results.append(msg)


.. function:: submit(gremlin, *, url='ws://localhost:8182/', bindings=None,
                     lang="gremlin-groovy", op="eval", processor="",
                     timeout=None, session=None, loop=None):

    :ref:`coroutine<coroutine>`

    Submit a script to the Gremlin Server.

    :param str gremlin: Gremlin script to submit to server.

    :param str url: url for Gremlin Server (optional). 'ws://localhost:8182/'
        by default

    :param dict bindings: A mapping of bindings for Gremlin script.

    :param str lang: Language of scripts submitted to the server.
        "gremlin-groovy" by default

    :param str op: Gremlin Server op argument. "eval" by default.

    :param str processor: Gremlin Server processor argument. "" by default.

    :param float timeout: timeout for establishing connection (optional).
        Values ``0`` or ``None`` mean no timeout

    :param str session: Session id (optional). Typically a uuid

    :param loop: :ref:`event loop<asyncio-event-loop>` If param is ``None``,
        `asyncio.get_event_loop` is used for getting default event loop
        (optional)

    :returns: :py:class:`aiogremlin.client.GremlinResponse` object


Reusing sockets with :py:class:`GremlinClient`
----------------------------------------------

To avoid the overhead of repeatedly establishing websocket connections,
``aiogremlin`` provides the class :py:class:`aiogremlin.client.GremlinClient`.
This class uses pooling to reuse websocket connections, and facilitates
concurrent message passing by yielding new websocket connections as needed::

    >>> client = aiogremlin.GremlinClient()
    >>> resp = client.submit("x + x", bindings={"x": 2})

For convenience, :py:class:`GremlinClient` provides the method
:py:meth:`aiogremlin.client.GremlinClient.execute`. This is equivalent of calling,
:py:meth:`GremlinClient.submit` and then :py:meth:`GremlinResponse.get`.
Therefore::

    >>> results = client.execute("x + x", bindings={"x": 2})

Is equivalent to::

    >>> resp = yield from aiogremlin.submit("x + x", bindings={"x": 2})
    >>> results = yield from resp.get()

:py:class:`GremlinClient` encapsulates :py:class:`aiogremlin.connector.GremlinConnector`.
This class produces the websocket connections used by the client, and handles all
of the connection pooling. It can also handle pools for multiple servers. To do
so, you can share a :py:class:`GremlinConnector` amongst various client that
point to different endpoints::

    >>> connector = aiogremlin.GremlinConnector()
    >>> client1 = aiogremlin.GremlinClient(url=url='ws://localhost:8182/'
    ...                                    ws_connector=connector)
    >>> client2 = aiogremlin.GremlinClient(url=url='ws://localhost:8080/'
    ...                                    ws_connector=connector)


.. class:: GremlinClient(self, *, url='ws://localhost:8182/', loop=None,
                         lang="gremlin-groovy", op="eval", processor="",
                         timeout=None, ws_connector=None)

    Main interface for interacting with the Gremlin Server.

    :param str url: url for Gremlin Server (optional). 'ws://localhost:8182/'
        by default

    :param loop: :ref:`event loop<asyncio-event-loop>` If param is ``None``,
        `asyncio.get_event_loop` is used for getting default event loop
        (optional)

    :param str lang: Language of scripts submitted to the server.
        "gremlin-groovy" by default

    :param str op: Gremlin Server op argument. "eval" by default

    :param str processor: Gremlin Server processor argument. "" by default

    :param float timeout: timeout for establishing connection (optional).
        Values ``0`` or ``None`` mean no timeout

    :param ws_connector: A class that implements the method :py:meth:`ws_connect`.
        Usually an instance of :py:class:`aiogremlin.connector.GremlinConnector`

.. method:: close()

   :ref:`coroutine<coroutine>` method

   Close client. If client has not been detached from underlying
   ws_connector, this coroutinemethod closes the latter as well.

.. method:: detach()

   Detach client from ws_connector. Client status is switched to closed.

.. method:: submit(gremlin, *, bindings=None, lang=None, op=None,
                   processor=None, binary=True, session=None, timeout=None)

   :ref:`coroutine<coroutine>` method

   Submit a script to the Gremlin Server.

   :param str gremlin: Gremlin script to submit to server.

   :param str url: url for Gremlin Server (optional). 'ws://localhost:8182/'
                   by default

   :param dict bindings: A mapping of bindings for Gremlin script.

   :param str lang: Language of scripts submitted to the server.
                    "gremlin-groovy" by default

   :param str op: Gremlin Server op argument. "eval" by default.

   :param str processor: Gremlin Server processor argument. "" by default.

   :param float timeout: timeout for establishing connection (optional).
                         Values ``0`` or ``None`` mean no timeout

   :param str session: Session id (optional). Typically a uuid

   :returns: :py:class:`aiogremlin.client.GremlinResponse` object

.. method:: execute(gremlin, *, bindings=None, lang=None, op=None,
                   processor=None, binary=True, session=None, timeout=None)

   :ref:`coroutine<coroutine>` method

   Submit a script to the Gremlin Server and get a list of the responses.

   :param str gremlin: Gremlin script to submit to server.

   :param str url: url for Gremlin Server (optional). 'ws://localhost:8182/'
                   by default

   :param dict bindings: A mapping of bindings for Gremlin script.

   :param str lang: Language of scripts submitted to the server.
                    "gremlin-groovy" by default

   :param str op: Gremlin Server op argument. "eval" by default.

   :param str processor: Gremlin Server processor argument. "" by default.

   :param float timeout: timeout for establishing connection (optional).
                         Values ``0`` or ``None`` mean no timeout

   :param str session: Session id (optional). Typically a uuid

   :returns: :py:class:`list` of :py:class:`aiogremlin.subprotocol.Message`


Using Gremlin Server sessions with :py:class:`GremlinClientSession`.
--------------------------------------------------------------------

The Gremlin Server supports sessions to maintain state across server
messages. Although this is not the preffered method, it is quite useful in
certain situations. For convenience, :py:mod:`aiogremlin` provides the class
:py:class:`aiogremlin.client.GremlinClientSession`. It is basically the
same as the :py:class:`GremlinClient`, but it uses sessions by default::

    >>> client = aiogremlin.GremlinClientSession()
    >>> client.session
    '533f15fb-dc2e-4768-86c5-5b136b380b65'
    >>> client.reset_session()
    'd7bdb0da-d4ec-4609-8ac0-df9713803d43'

That's basically it! For more info, see the
:ref:`Client Reference Guide<aiogremlin-client-reference>`










.. _Gremlin Server: http://tinkerpop.incubator.apache.org/
