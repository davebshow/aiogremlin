"""
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
"""
import abc
import base64
import collections
import uuid

try:
    import ujson as json
except ImportError:
    import json


__author__ = 'David M. Brown (davebshow@gmail.com)'


class AbstractBaseProtocol(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def connection_made(self, transport):
        self._transport = transport

    @abc.abstractmethod
    def data_received(self, message):
        pass

    @abc.abstractmethod
    def write(self, request_id, request_message):
        pass
