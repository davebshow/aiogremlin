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
import os

import pytest

from aiogremlin import driver, exception
from aiogremlin.gremlin_python.driver import serializer

import config_module


dirname = os.path.dirname(os.path.dirname(__file__))


@pytest.fixture(params=[0, 1])
def conf_module(request):
    if request.param:
        return 'config_module'
    else:
        return config_module


def test_cluster_default_config(event_loop):
    cluster = driver.Cluster(event_loop)
    assert cluster.config['scheme'] == 'ws'
    assert cluster.config['hosts'] == ['localhost']
    assert cluster.config['port'] == 8182
    assert cluster.config['ssl_certfile'] == ''
    assert cluster.config['ssl_keyfile'] == ''
    assert cluster.config['ssl_password'] == ''
    assert cluster.config['username'] == ''
    assert cluster.config['password'] == ''


def test_cluster_custom_config(event_loop, cluster_class):
    cluster = cluster_class(event_loop, username='dave', password='mypass',
                            hosts=['127.0.0.1'])
    assert cluster.config['scheme'] == 'ws'
    assert cluster.config['hosts'] == ['127.0.0.1']
    assert cluster.config['port'] == 8182
    assert cluster.config['ssl_certfile'] == ''
    assert cluster.config['ssl_keyfile'] == ''
    assert cluster.config['ssl_password'] == ''
    assert cluster.config['username'] == 'dave'
    assert cluster.config['password'] == 'mypass'
    assert issubclass(cluster.config['message_serializer'],
                      serializer.GraphSONMessageSerializer)


def test_cluster_config_from_json(event_loop, cluster_class):
    cluster = cluster_class(event_loop)
    cluster.config_from_file(dirname + '/tests/config/config.json')
    assert cluster.config['scheme'] == 'wss'
    assert cluster.config['hosts'] == ['localhost']
    assert cluster.config['port'] == 8182
    assert cluster.config['ssl_certfile'] == ''
    assert cluster.config['ssl_keyfile'] == ''
    assert cluster.config['ssl_password'] == ''
    assert cluster.config['username'] == 'dave'
    assert cluster.config['password'] == 'mypass'

    assert issubclass(cluster.config['message_serializer'],
                      serializer.GraphSONMessageSerializer)


def test_cluster_config_from_yaml(event_loop, cluster_class):
    cluster = cluster_class(event_loop)
    cluster.config_from_file(dirname + '/tests/config/config.yml')
    assert cluster.config['scheme'] == 'wss'
    assert cluster.config['hosts'] == ['localhost']
    assert cluster.config['port'] == 8183
    assert cluster.config['ssl_certfile'] == ''
    assert cluster.config['ssl_keyfile'] == ''
    assert cluster.config['ssl_password'] == ''
    assert cluster.config['username'] == ''
    assert cluster.config['password'] == ''
    assert issubclass(cluster.config['message_serializer'],
                      serializer.GraphSONMessageSerializer)


def test_cluster_config_from_module(event_loop, cluster_class, conf_module):
    cluster = cluster_class(event_loop)
    cluster.config_from_module(conf_module)
    assert cluster.config['scheme'] == 'wss'
    assert cluster.config['hosts'] == ['localhost']
    assert cluster.config['port'] == 8183
    assert cluster.config['message_serializer'] is serializer.GraphSONMessageSerializer
