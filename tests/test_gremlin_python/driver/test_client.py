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

from aiogremlin.gremlin_python.driver.request import RequestMessage
from aiogremlin.gremlin_python.structure.graph import Graph

__author__ = 'David M. Brown (davebshow@gmail.com)'


@pytest.mark.asyncio
async def test_connection(connection):
    g = Graph().traversal()
    t = g.V()
    message = RequestMessage('traversal', 'bytecode', {'gremlin': t.bytecode})
    results_set = await connection.write(message)
    results = await results_set.all()
    assert len(results) == 6
    assert isinstance(results, list)
    await connection.close()


@pytest.mark.asyncio
async def test_client_simple_eval(client):
    result_set = await client.submit('1 + 1')
    results = await result_set.all()
    assert results[0] == 2
    await client.close()


@pytest.mark.asyncio
async def test_client_simple_eval_bindings(client):
    result_set = await client.submit('x + x', {'x': 2})
    results = await result_set.all()
    assert results[0] == 4
    await client.close()

@pytest.mark.asyncio
async def test_client_eval_traversal(client):
    result_set = await client.submit('g.V()')
    results = await result_set.all()
    assert len(results) == 6
    await client.close()


@pytest.mark.asyncio
async def test_client_bytecode(client):
    g = Graph().traversal()
    t = g.V()
    message = RequestMessage('traversal', 'bytecode', {'gremlin': t.bytecode})
    result_set = await client.submit(message)
    results = await result_set.all()
    assert len(results) == 6
    await client.close()

@pytest.mark.asyncio
async def test_iterate_result_set(client):
    g = Graph().traversal()
    t = g.V()
    message = RequestMessage('traversal', 'bytecode', {'gremlin': t.bytecode})
    result_set = await client.submit(message)
    results = []
    async for result in result_set:
        results.append(result)
    assert len(results) == 6
    await client.close()
