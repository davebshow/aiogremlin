'''
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
'''
'''THIS FILE HAS BEEN MODIFIED BY DAVID M. BROWN TO SUPPORT PEP 492'''
import pytest

from aiogremlin.remote.driver_remote_connection import (
    DriverRemoteConnection)
from aiogremlin.driver.protocol import GremlinServerWSProtocol
from aiogremlin.driver.aiohttp.transport import AiohttpTransport
from aiogremlin.gremlin_python.driver.serializer import GraphSONMessageSerializer


@pytest.fixture
def client(event_loop, cluster):
    try:
        client = event_loop.run_until_complete(cluster.connect())
    except OSError:
        pytest.skip('Gremlin Server is not running')
    else:
        return client

@pytest.fixture
def remote_connection(event_loop, gremlin_url):
    try:
        remote_conn = event_loop.run_until_complete(
            DriverRemoteConnection.open(gremlin_url, 'g'))
    except OSError:
        pytest.skip('Gremlin Server is not running')
    else:
        return remote_conn
