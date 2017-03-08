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
import abc
import collections

from aiogremlin.gremlin_python.driver import request
from aiogremlin.gremlin_python.process import traversal

__author__ = 'Marko A. Rodriguez (http://markorodriguez.com)'


class RemoteConnection(metaclass=abc.ABCMeta):
    def __init__(self, url, traversal_source):
        self._url = url
        self._traversal_source = traversal_source

    @property
    def url(self):
        return self._url

    @property
    def traversal_source(self):
        return self._traversal_source

    @abc.abstractmethod
    def submit(self, bytecode):
        pass

    def __repr__(self):
        return "remoteconnection[" + self._url + "," + self._traversal_source + "]"


class RemoteTraversal(traversal.Traversal):
    def __init__(self, traversers, side_effects):
        super(RemoteTraversal, self).__init__(None, None, None)
        self.traversers = traversers
        self._side_effects = side_effects

    @property
    def side_effects(self):
        return self._side_effects

    @side_effects.setter
    def side_effects(self, val):
        self._side_effects = val


class RemoteStrategy(traversal.TraversalStrategy):
    def __init__(self, remote_connection):
        self.remote_connection = remote_connection

    async def apply(self, traversal):
        if traversal.traversers is None:
            remote_traversal = await self.remote_connection.submit(
                traversal.bytecode)
            traversal.remote_results = remote_traversal
            traversal.side_effects = remote_traversal.side_effects
            traversal.traversers = remote_traversal.traversers
