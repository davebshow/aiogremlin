# Copyright 2016 David M. Brown
#
# This file is part of Goblin.
#
# Goblin is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Goblin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Goblin.  If not, see <http://www.gnu.org/licenses/>.
import asyncio
import pytest
from aiogremlin import driver
from aiogremlin.driver.provider import TinkerGraph
from aiogremlin.gremlin_python.driver import serializer


# def pytest_generate_tests(metafunc):
#     if 'cluster' in metafunc.fixturenames:
#         metafunc.parametrize("cluster", ['c1', 'c2'], indirect=True)


def pytest_addoption(parser):
    parser.addoption('--provider', default='tinkergraph',
                     choices=('tinkergraph', 'dse',))
    parser.addoption('--gremlin-host', default='localhost')
    parser.addoption('--gremlin-port', default='8182')


@pytest.fixture
def provider(request):
    provider = request.config.getoption('provider')
    if provider == 'tinkergraph':
        return TinkerGraph
    elif provider == 'dse':
        try:
            import goblin_dse
        except ImportError:
            raise RuntimeError("Couldn't run tests with DSEGraph provider: the goblin_dse package "
                               "must be installed")
        else:
            return goblin_dse.DSEGraph


@pytest.fixture
def aliases(request):
    if request.config.getoption('provider') == 'tinkergraph':
        return {'g': 'g'}
    elif request.config.getoption('provider') == 'dse':
        return {'g': 'testgraph.g'}


@pytest.fixture
def gremlin_server():
    return driver.GremlinServer


@pytest.fixture
def unused_server_url(unused_tcp_port):
    return 'http://localhost:{}/gremlin'.format(unused_tcp_port)


@pytest.fixture
def gremlin_host(request):
    return request.config.getoption('gremlin_host')


@pytest.fixture
def gremlin_port(request):
    return request.config.getoption('gremlin_port')


@pytest.fixture
def gremlin_url(gremlin_host, gremlin_port):
    return "http://{}:{}/gremlin".format(gremlin_host, gremlin_port)


@pytest.fixture
def connection(gremlin_url, event_loop, provider):
    try:
        conn = event_loop.run_until_complete(
            driver.Connection.open(
                gremlin_url, event_loop,
                message_serializer=serializer.GraphSONMessageSerializer,
                provider=provider
            ))
    except OSError:
        pytest.skip('Gremlin Server is not running')
    return conn


@pytest.fixture
def connection_pool(gremlin_url, event_loop, provider):
    return driver.ConnectionPool(
        gremlin_url, event_loop, None, '', '', 4, 1, 16,
        64, None, serializer.GraphSONMessageSerializer, provider=provider)


@pytest.fixture
def cluster(request, gremlin_host, gremlin_port, event_loop, provider, aliases):
    # if request.param == 'c1':
    cluster = driver.Cluster(
        event_loop,
        hosts=[gremlin_host],
        port=gremlin_port,
        aliases=aliases,
        message_serializer=serializer.GraphSONMessageSerializer,
        provider=provider
    )
    # elif request.param == 'c2':
    #     cluster = driver.Cluster(
    #         event_loop,
    #         hosts=[gremlin_host],
    #         port=gremlin_port,
    #         aliases=aliases,
    #         message_serializer=serializer.GraphSONMessageSerializer,
    #         provider=provider
    #     )
    return cluster

# TOOO FIX
# @pytest.fixture
# def remote_graph():
#      return driver.AsyncGraph()

# Class fixtures
@pytest.fixture
def cluster_class(event_loop):
    return driver.Cluster
