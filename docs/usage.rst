Using :py:mod:`aiogremlin`
==========================

Before you get started, make sure you have the Gremlin Server up and running.
All of the following example assume a running Gremlin Server version 3.2.4 at
`ws://localhost:8182/gremlin` using the `conf/gremlin-server-modern-py.yaml`
configuration::

    $ ./bin/gremlin-server.sh conf/gremlin-server-modern-py.yaml


Using the Gremlin Language Variant
----------------------------------

:py:mod:`aiogremlin` is used almost exactly like the official Gremlin-Python,
except that all operations are asynchronous. Thus when coding with :py:mod:`aiogremlin`
coroutines and the `async/await` syntax are used in combination with an `asyncio` compatible
event loop implementation (`tornado`, `ZeroMQ`, `uvloop`, etc.).

The following examples assume that you are already familiar with `asyncio`, coroutines,
and the event loop. For readability, they strip away these details
to focus on the syntax used by :py:mod:`aiogremlin`.

To create a traversal source, simply use
:py:class:`DriverRemoteConnection<aiogremlin.remote.driver_remote_connection.DriverRemoteConnection>`
combined with :py:class:`Graph<aiogremlin.gremlin_python.structure.graph.Graph>`::

    >>> remote_connection = await DriverRemoteConnection.open(
    ...    'ws://localhost:8182/gremlin', 'g')
    >>>  g = Graph().traversal().withRemote(remote_connection)

In :py:mod:`aiogremlin`, a
:py:class:`Traversal<aiogremlin.gremlin_python.process.traversal.Traversal>`
implements the Asynchronous Iterator Protocol as defined
by PEP 492::

    >>> async for vertex in g.V():
    ...     print(vertex)

Furthermore, it implements several convience methods - :py:meth:`toList`,
:py:meth:`toSet`, and :py:meth:`next`::

    >>> vertex_list = await g.V().toList()
    >>> vertex_set = await g.V().toSet()
    >>> next_vertex = await g.V().next() # returns next result from the stream

:py:class:`Traversal<aiogremlin.gremlin_python.process.traversal.Traversal>`
also contains a reference to a
:py:class:`RemoteTraversalSideEffects<aiogremlin.remote.driver_remote_side_effects.RemoteTraversalSideEffects>`
object that can be used to fetch side effects cached by the server (when applicable)::

    >>> t = g.V().aggregate('a')
    >>> await t.iterate()  # evaluate the traversal
    >>> keys = await t.side_effects.keys()
    >>> se = await t.side_effects.get('a')
    >>> await t.side_effects.close()

Don't forget to close the
:py:class:`DriverRemoteConnection<aiogremlin.remote.driver_remote_connection.DriverRemoteConnection>`
when finished::

    >>> await remote_connection.close()


Using :py:class:`DriverRemoteConnection<aiogremlin.remote.driver_remote_connection.DriverRemoteConnection>`
-----------------------------------------------------------------------------------------------------------

The
:py:class:`DriverRemoteConnection<aiogremlin.remote.driver_remote_connection.DriverRemoteConnection>`
object allows you to configure you database connection in one of two ways:

1. Passing configuration values as kwargs or a :py:class:`dict` to the classmethod
:py:meth:`open<aiogremlin.remote.driver_remote_connection.DriverRemoteConnection.open>`::

    >>> remote_connection = await DriverRemoteConnection.open(
    ...    'ws://localhost:8182/gremlin', 'g', port=9430)

2. Passing a :py:class:`Cluster<aiogremlin.driver.cluster.Cluster>` object to the
classmethod
:py:meth:`using<aiogremlin.remote.driver_remote_connection.DriverRemoteConnection.using>`::

    >>> import asyncio
    >>> from aiogremlin import Cluster
    >>> loop = asyncio.get_event_loop()
    >>> cluster = await Cluster.open(loop, port=9430, aliases={'g': 'g'})
    >>> remote_connection = await DriverRemoteConnection.using(cluster)

In the case that the
:py:class:`DriverRemoteConnection<aiogremlin.remote.driver_remote_connection.DriverRemoteConnection>`
is created with
:py:meth:`using<aiogremlin.remote.driver_remote_connection.DriverRemoteConnection.using>`,
it is not necessary to close the
:py:class:`DriverRemoteConnection<aiogremlin.remote.driver_remote_connection.DriverRemoteConnection>`,
but the underlying :py:class:`Cluster<aiogremlin.driver.cluster.Cluster>` must be closed::

    >>> await cluster.close()

Configuration options are specified in the final section of this document.

:py:class:`DriverRemoteConnection<aiogremlin.remote.driver_remote_connection.DriverRemoteConnection>`
is also an asynchronous context manager. It can be used as follows::

    >>> async with remote_connection:
    ...     g = Graph().traversal().withRemote(remote_connection)
    ...     # traverse
    # remote_connection is closed upon exit

Taking this one step further, the
:py:meth:`open<aiogremlin.remote.driver_remote_connection.DriverRemoteConnection.open>`
can be awaited in the async context manager statement::

    >>> async with await DriverRemoteConnection.open() as remote_connection:
    ...     g = Graph().traversal().withRemote(remote_connection)
    ...     # traverse
    # remote connection is closed upon exit

Using the :py:mod:`driver<aiogremlin.driver>` Module
----------------------------------------------------

:py:mod:`aiogremlin` also includes an asynchronous driver modeled after the
official Gremlin-Python driver implementation. However, instead of using
threads for asynchronous I/O, it uses an :py:mod:`asyncio` based implemenation.

To submit a raw Gremlin script to the server, use the
:py:class:`Client<aiogremlin.driver.client.Client>`. This class should not
be instantiated directly, instead use a
:py:class:`Cluster<aiogremlin.driver.cluster.Cluster>` object::

    >>> cluster = await Cluster.open(loop)
    >>> client = await cluster.connect()
    >>> result_set = await client.submit('g.V().hasLabel(x)', {'x': 'person'})

The :py:class:`ResultSet<aiogremlin.driver.resultset.ResultSet>` returned by
:py:meth:`Client<aiogremlin.driver.client.Client.submit>` implements the
async interator protocol::

    >>> async for v in result_set:
    ...     print(v)

It also provides a convenience method
:py:meth:`all<aiogremlin.driver.client.Client.all>`
that aggregates and returns the result of the script in a :py:class:`list`::

    >>> results = await result_set.all()

Closing the client will close the underlying cluster::

    >>> await client.close()

Configuring the :py:class:`Cluster<aiogremlin.driver.cluster.Cluster>` object
-----------------------------------------------------------------------------

Configuration options can be set on
:py:class:`Cluster<aiogremlin.driver.cluster.Cluster>` in one of two ways, either
passed as keyword arguments to
:py:meth:`Cluster<aiogremlin.driver.cluster.Cluster.open>`, or stored in a configuration
file and passed to the :py:meth:`open<aiogremlin.driver.cluster.Cluster.open>`
using the kwarg `configfile`. Configuration files can be either YAML or JSON
format. Currently, :py:class:`Cluster<aiogremlin.driver.cluster.Cluster>`
uses the following configuration:

+-------------------+----------------------------------------------+-------------+
|Key                |Description                                   |Default      |
+===================+==============================================+=============+
|scheme             |URI scheme, typically 'ws' or 'wss' for secure|'ws'         |
|                   |websockets                                    |             |
+-------------------+----------------------------------------------+-------------+
|hosts              |A list of hosts the cluster will connect to   |['localhost']|
+-------------------+----------------------------------------------+-------------+
|port               |The port of the Gremlin Server to connect to, |8182         |
|                   |same for all hosts                            |             |
+-------------------+----------------------------------------------+-------------+
|ssl_certfile       |File containing ssl certificate               |''           |
+-------------------+----------------------------------------------+-------------+
|ssl_keyfile        |File containing ssl key                       |''           |
+-------------------+----------------------------------------------+-------------+
|ssl_password       |File containing password for ssl keyfile      |''           |
+-------------------+----------------------------------------------+-------------+
|username           |Username for Gremlin Server authentication    |''           |
+-------------------+----------------------------------------------+-------------+
|password           |Password for Gremlin Server authentication    |''           |
+-------------------+----------------------------------------------+-------------+
|response_timeout   |Timeout for reading responses from the stream |`None`       |
+-------------------+----------------------------------------------+-------------+
|max_conns          |The maximum number of connections open at any |4            |
|                   |time to this host                             |             |
+-------------------+----------------------------------------------+-------------+
|min_conns          |The minimum number of connection open at any  |1            |
|                   |time to this host                             |             |
+-------------------+----------------------------------------------+-------------+
|max_times_acquired |The maximum number of times a single pool     |16           |
|                   |connection can be acquired and shared         |             |
+-------------------+----------------------------------------------+-------------+
|max_inflight       |The maximum number of unresolved messages     |64           |
|                   |that may be pending on any one connection     |             |
+-------------------+----------------------------------------------+-------------+
|message_serializer |String denoting the class used for message    |'classpath'  |
|                   |serialization, currently only supports        |             |
|                   |basic GraphSONMessageSerializer               |             |
+-------------------+----------------------------------------------+-------------+
