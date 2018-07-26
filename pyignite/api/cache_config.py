# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Set of functions to manipulate caches.

Ignite `cache` can be viewed as a named entity designed to store key-value
pairs. Each cache is split transparently between different Ignite partitions.

The choice of `cache` term is due to historical reasons. (Ignite initially had
only non-persistent storage tier.)
"""

from typing import Union

from pyignite.connection import Connection
from pyignite.datatypes.cache_config import cache_config_struct
from pyignite.datatypes.cache_properties import prop_map
from pyignite.datatypes import Int, Byte, Short, String, StringArray
from pyignite.queries import Query, ConfigQuery, Response
from pyignite.queries.op_codes import *
from pyignite.utils import cache_id
from .result import APIResult


def cache_get_configuration(
    conn: Connection, cache: Union[str, int], flags: int=0, query_id=None,
) -> APIResult:
    """
    Gets configuration for the given cache.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param flags: Ignite documentation is unclear on this subject,
    :param query_id: (optional) a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Result value is OrderedDict with
     the cache configuration parameters.
    """

    class CacheGetConfigurationQuery(Query):
        op_code = OP_CACHE_GET_CONFIGURATION

    query_struct = CacheGetConfigurationQuery([
        ('hash_code', Int),
        ('flags', Byte),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flags': flags,
    })
    conn.send(send_buffer)

    response_struct = Response([
        ('cache_config', cache_config_struct),
    ])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)
    result = APIResult(response)
    if result.status != 0:
        return result
    result.value = response_struct.to_python(response)['cache_config']
    return result


def cache_create(conn: Connection, name: str, query_id=None,) -> APIResult:
    """
    Creates a cache with a given name. Returns error if a cache with specified
    name already exists.

    :param conn: connection to Ignite server,
    :param name: cache name,
    :param query_id: (optional) a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status if a cache is
     created successfully, non-zero status and an error description otherwise.
    """

    class CacheCreateQuery(Query):
        op_code = OP_CACHE_CREATE_WITH_NAME

    query_struct = CacheCreateQuery([
        ('cache_name', String),
    ], query_id=query_id)
    _, send_buffer = query_struct.from_python({'cache_name': name})
    conn.send(send_buffer)

    response_struct = Response([])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)
    result = APIResult(response)
    return result


def cache_get_or_create(conn: Connection, name: str, query_id=None,) -> APIResult:
    """
    Creates a cache with a given name. Does nothing if the cache exists.

    :param conn: connection to Ignite server,
    :param name: cache name,
    :param query_id: (optional) a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status if a cache is
     created successfully, non-zero status and an error description otherwise.
    """

    class CacheGetOrCreateQuery(Query):
        op_code = OP_CACHE_GET_OR_CREATE_WITH_NAME

    query_struct = CacheGetOrCreateQuery([
        ('cache_name', String),
    ], query_id=query_id)
    _, send_buffer = query_struct.from_python({'cache_name': name})
    conn.send(send_buffer)

    response_struct = Response([])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)
    result = APIResult(response)
    return result


def cache_destroy(
    conn: Connection, cache: Union[str, int], query_id=None,
) -> APIResult:
    """
    Destroys cache with a given name.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param query_id: (optional) a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object.
    """

    class CacheDestroyQuery(Query):
        op_code = OP_CACHE_DESTROY

    query_struct = CacheDestroyQuery([
        ('hash_code', Int),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
    })
    conn.send(send_buffer)

    response_struct = Response([])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)
    result = APIResult(response)
    return result


def cache_get_names(conn: Connection, query_id=None) -> APIResult:
    """
    Gets existing cache names.

    :param conn: connection to Ignite server,
    :param query_id: (optional) a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status and a list of cache
     names, non-zero status and an error description otherwise.
    """

    class CacheGetNamesQuery(Query):
        op_code = OP_CACHE_GET_NAMES

    query_struct = CacheGetNamesQuery(query_id=query_id)

    _, send_buffer = query_struct.from_python()
    conn.send(send_buffer)

    response_struct = Response([
        ('cache_names', StringArray),
    ])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)
    result = APIResult(response)
    if result.status != 0:
        return result
    result.value = response_struct.to_python(response)['cache_names']
    return result


def cache_create_with_config(
    conn: Connection, cache_props: dict, query_id=None,
) -> APIResult:
    """
    Creates cache with provided configuration. An error is returned
    if the name is already in use.

    :param conn: connection to Ignite server,
    :param cache_props: cache configuration properties to create cache with
     in form of dictionary {property code: python value}.
     You must supply at least name (PROP_NAME),
    :param query_id: (optional) a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status if cache was created,
     non-zero status and an error description otherwise.
    """

    class CacheCreateWithConfigQuery(ConfigQuery):
        op_code = OP_CACHE_CREATE_WITH_CONFIGURATION

    prop_types = {}
    prop_values = {}
    for i, prop_item in enumerate(cache_props.items()):
        prop_code, prop_value = prop_item
        prop_name = 'property_{}'.format(i)
        prop_types[prop_name] = prop_map(prop_code)
        prop_values[prop_name] = prop_value
    prop_values['param_count'] = len(cache_props)

    query_struct = CacheCreateWithConfigQuery([
        ('param_count', Short),
    ] + list(prop_types.items()), query_id=query_id)

    _, send_buffer = query_struct.from_python(prop_values)
    conn.send(send_buffer)

    response_struct = Response([])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)
    result = APIResult(response)
    return result


def cache_get_or_create_with_config(
    conn: Connection, cache_props: dict, query_id=None,
) -> APIResult:
    """
    Creates cache with provided configuration. Does nothing if the name
    is already in use.

    :param conn: connection to Ignite server,
    :param cache_props: cache configuration properties to create cache with
     in form of dictionary {property code: python value}.
     You must supply at least name (PROP_NAME),
    :param query_id: (optional) a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status if cache was created,
     non-zero status and an error description otherwise.
    """

    class CacheGetOrCreateWithConfigQuery(ConfigQuery):
        op_code = OP_CACHE_GET_OR_CREATE_WITH_CONFIGURATION

    prop_types = {}
    prop_values = {}
    for i, prop_item in enumerate(cache_props.items()):
        prop_code, prop_value = prop_item
        prop_name = 'property_{}'.format(i)
        prop_types[prop_name] = prop_map(prop_code)
        prop_values[prop_name] = prop_value
    prop_values['param_count'] = len(cache_props)

    query_struct = CacheGetOrCreateWithConfigQuery([
        ('param_count', Short),
    ] + list(prop_types.items()), query_id=query_id)

    _, send_buffer = query_struct.from_python(prop_values)
    conn.send(send_buffer)

    response_struct = Response([])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)
    result = APIResult(response)
    return result
