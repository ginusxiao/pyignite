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

from typing import Union

from pyignite.connection import Connection
from pyignite.queries.op_codes import *
from pyignite.datatypes import (
    Map, Bool, Byte, Int, Long, AnyDataArray, AnyDataObject,
)
from pyignite.datatypes.key_value import PeekModes
from pyignite.queries import Query, Response
from .result import APIResult
from pyignite.utils import cache_id


def cache_put(
    conn: Connection, cache: Union[str, int], key, value,
    key_hint=None, value_hint=None, binary=False, query_id=None,
) -> APIResult:
    """
    Puts a value with a given key to cache (overwriting existing value if any).

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param key: key for the cache entry. Can be of any supported type,
    :param value: value for the key,
    :param key_hint: (optional) Ignite data type, for which the given key
     should be converted,
    :param value_hint: (optional) Ignite data type, for which the given value
     should be converted.
    :param binary: (optional) pass True to keep the value in binary form.
     False by default,
    :param query_id: (optional) a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status if a value
     is written, non-zero status and an error description otherwise.
    """

    class CachePutQuery(Query):
        op_code = OP_CACHE_PUT

    query_struct = CachePutQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('key', key_hint or AnyDataObject),
        ('value', value_hint or AnyDataObject),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'key': key,
        'value': value,
    })

    conn.send(send_buffer)

    response_struct = Response([])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    if result.status != 0:
        return result
    result.value = response_struct.to_python(response)
    return result


def cache_get(
    conn: Connection, cache: Union[str, int], key,
    key_hint=None, binary=False, query_id=None,
) -> APIResult:
    """
    Retrieves a value from cache by key.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param key: key for the cache entry. Can be of any supported type,
    :param key_hint: (optional) Ignite data type, for which the given key
     should be converted,
    :param binary: (optional) pass True to keep the value in binary form.
     False by default,
    :param query_id: (optional) a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status and a value
     retrieved on success, non-zero status and an error description on failure.
    """

    class CacheGetQuery(Query):
        op_code = OP_CACHE_GET

    query_struct = CacheGetQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('key', key_hint or AnyDataObject),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'key': key,
    })

    conn.send(send_buffer)

    response_struct = Response([
        ('value', AnyDataObject),
    ])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    if result.status != 0:
        return result
    result.value = response_struct.to_python(response)['value']
    return result


def cache_get_all(
    conn: Connection, cache: Union[str, int], keys: list, binary=False,
    query_id=None,
) -> APIResult:
    """
    Retrieves multiple key-value pairs from cache.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param keys: list of keys or tuples of (key, key_hint),
    :param binary: (optional) pass True to keep the value in binary form.
     False by default,
    :param query_id: (optional) a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status and a dict, made of
     retrieved key-value pairs, non-zero status and an error description
     on failure.
    """

    class CacheGetAllQuery(Query):
        op_code = OP_CACHE_GET_ALL

    query_struct = CacheGetAllQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('keys', AnyDataArray()),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'keys': keys,
    })
    conn.send(send_buffer)

    response_struct = Response([
        ('data', Map),
    ])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    if result.status != 0:
        return result
    result.value = dict(response_struct.to_python(response))['data']
    return result


def cache_put_all(
    conn: Connection, cache: Union[str, int], pairs: dict, binary=False, query_id=None,
) -> APIResult:
    """
    Puts multiple key-value pairs to cache (overwriting existing associations
    if any).

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param pairs: dictionary type parameters, contains key-value pairs to save.
     Each key or value can be an item of representable Python type or a tuple
     of (item, hint),
    :param binary: (optional) pass True to keep the value in binary form.
     False by default,
    :param query_id: (optional) a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status if key-value pairs
     are written, non-zero status and an error description otherwise.
    """

    class CachePutAllQuery(Query):
        op_code = OP_CACHE_PUT_ALL

    query_struct = CachePutAllQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('data', Map),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'data': pairs,
    })
    conn.send(send_buffer)

    response_struct = Response([])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    return result


def cache_contains_key(
    conn: Connection, cache: Union[str, int], key,
    key_hint=None, binary=False, query_id=None,
) -> APIResult:
    """
    Returns a value indicating whether given key is present in cache.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param key: key for the cache entry. Can be of any supported type,
    :param key_hint: (optional) Ignite data type, for which the given key
     should be converted,
    :param binary: pass True to keep the value in binary form. False
     by default,
    :param query_id: a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status and a bool value
     retrieved on success: `True` when key is present, `False` otherwise,
     non-zero status and an error description on failure.
    """

    class CacheContainsKeyQuery(Query):
        op_code = OP_CACHE_CONTAINS_KEY

    query_struct = CacheContainsKeyQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('key', key_hint or AnyDataObject),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'key': key,
    })

    conn.send(send_buffer)

    response_struct = Response([
        ('value', Bool),
    ])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    if result.status != 0:
        return result
    result.value = response_struct.to_python(response)['value']
    return result


def cache_contains_keys(
    conn: Connection, cache: Union[str, int], keys, binary=False, query_id=None,
) -> APIResult:
    """
    Returns a value indicating whether all given keys are present in cache.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param keys:
    :param binary: pass True to keep the value in binary form. False
     by default,
    :param query_id: a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status and a bool value
     retrieved on success: `True` when all keys are present, `False` otherwise,
     non-zero status and an error description on failure.
    """

    class CacheContainsKeysQuery(Query):
        op_code = OP_CACHE_CONTAINS_KEYS

    query_struct = CacheContainsKeysQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('keys', AnyDataArray()),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'keys': keys,
    })
    conn.send(send_buffer)

    response_struct = Response([
        ('value', Bool),
    ])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    if result.status != 0:
        return result
    result.value = response_struct.to_python(response)['value']
    return result


def cache_get_and_put(
    conn: Connection, cache: Union[str, int], key, value,
    key_hint=None, value_hint=None, binary=False, query_id=None,
) -> APIResult:
    """
    Puts a value with a given key to cache, and returns the previous value
    for that key, or null value if there was not such key.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param key: key for the cache entry. Can be of any supported type,
    :param value: value for the key,
    :param key_hint: (optional) Ignite data type, for which the given key
     should be converted,
    :param value_hint: (optional) Ignite data type, for which the given value
     should be converted.
    :param binary: pass True to keep the value in binary form. False
     by default,
    :param query_id: a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status and an old value
     or None if a value is written, non-zero status and an error description
     in case of error.
    """

    class CacheGetAndPutQuery(Query):
        op_code = OP_CACHE_GET_AND_PUT

    query_struct = CacheGetAndPutQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('key', key_hint or AnyDataObject),
        ('value', value_hint or AnyDataObject),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'key': key,
        'value': value,
    })

    conn.send(send_buffer)

    response_struct = Response([
        ('value', AnyDataObject),
    ])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    if result.status != 0:
        return result
    result.value = response_struct.to_python(response)['value']
    return result


def cache_get_and_replace(
    conn: Connection, cache: Union[str, int], key, value,
    key_hint=None, value_hint=None, binary=False, query_id=None,
) -> APIResult:
    """
    Puts a value with a given key to cache, returning previous value
    for that key, if and only if there is a value currently mapped
    for that key.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param key: key for the cache entry. Can be of any supported type,
    :param value: value for the key,
    :param key_hint: (optional) Ignite data type, for which the given key
     should be converted,
    :param value_hint: (optional) Ignite data type, for which the given value
     should be converted.
    :param binary: pass True to keep the value in binary form. False
     by default,
    :param query_id: a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status and an old value
     or None on success, non-zero status and an error description otherwise.
    """

    class CacheGetAndReplaceQuery(Query):
        op_code = OP_CACHE_GET_AND_REPLACE

    query_struct = CacheGetAndReplaceQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('key', key_hint or AnyDataObject),
        ('value', value_hint or AnyDataObject),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'key': key,
        'value': value,
    })

    conn.send(send_buffer)

    response_struct = Response([
        ('value', AnyDataObject),
    ])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    if result.status != 0:
        return result
    result.value = response_struct.to_python(response)['value']
    return result


def cache_get_and_remove(
    conn: Connection, cache: Union[str, int], key,
    key_hint=None, binary=False, query_id=None,
) -> APIResult:
    """
    Removes the cache entry with specified key, returning the value.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param key: key for the cache entry. Can be of any supported type,
    :param key_hint: (optional) Ignite data type, for which the given key
     should be converted,
    :param binary: pass True to keep the value in binary form. False
     by default,
    :param query_id: a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status and an old value
     or None, non-zero status and an error description otherwise.
    """

    class CacheGetAndRemoveQuery(Query):
        op_code = OP_CACHE_GET_AND_REMOVE

    query_struct = CacheGetAndRemoveQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('key', key_hint or AnyDataObject),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'key': key,
    })

    conn.send(send_buffer)

    response_struct = Response([
        ('value', AnyDataObject),
    ])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    if result.status != 0:
        return result
    result.value = response_struct.to_python(response)['value']
    return result


def cache_put_if_absent(
    conn: Connection, cache: Union[str, int], key, value,
    key_hint=None, value_hint=None, binary=False, query_id=None,
) -> APIResult:
    """
    Puts a value with a given key to cache only if the key
    does not already exist.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param key: key for the cache entry. Can be of any supported type,
    :param value: value for the key,
    :param key_hint: (optional) Ignite data type, for which the given key
     should be converted,
    :param value_hint: (optional) Ignite data type, for which the given value
     should be converted.
    :param binary: (optional) pass True to keep the value in binary form. False
     by default,
    :param query_id: (optional) a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status on success,
     non-zero status and an error description otherwise.
    """

    class CachePutIfAbsentQuery(Query):
        op_code = OP_CACHE_PUT_IF_ABSENT

    query_struct = CachePutIfAbsentQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('key', key_hint or AnyDataObject),
        ('value', value_hint or AnyDataObject),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'key': key,
        'value': value,
    })

    conn.send(send_buffer)

    response_struct = Response([
        ('success', Bool),
    ])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    if result.status != 0:
        return result
    result.value = response_struct.to_python(response)['success']
    return result


def cache_get_and_put_if_absent(
    conn: Connection, cache: Union[str, int], key, value,
    key_hint=None, value_hint=None, binary=False, query_id=None,
) -> APIResult:
    """
    Puts a value with a given key to cache only if the key does not
    already exist.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param key: key for the cache entry. Can be of any supported type,
    :param value: value for the key,
    :param key_hint: (optional) Ignite data type, for which the given key
     should be converted,
    :param value_hint: (optional) Ignite data type, for which the given value
     should be converted.
    :param binary: (optional) pass True to keep the value in binary form. False
     by default,
    :param query_id: (optional) a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status and an old value
     or None on success, non-zero status and an error description otherwise.
    """

    class CacheGetAndPutIfAbsentQuery(Query):
        op_code = OP_CACHE_GET_AND_PUT_IF_ABSENT

    query_struct = CacheGetAndPutIfAbsentQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('key', key_hint or AnyDataObject),
        ('value', value_hint or AnyDataObject),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'key': key,
        'value': value,
    })

    conn.send(send_buffer)

    response_struct = Response([
        ('value', AnyDataObject),
    ])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    if result.status != 0:
        return result
    result.value = response_struct.to_python(response)['value']
    return result


def cache_replace(
    conn: Connection, cache: Union[str, int], key, value,
    key_hint=None, value_hint=None, binary=False, query_id=None,
) -> APIResult:
    """
    Puts a value with a given key to cache only if the key already exist.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param key: key for the cache entry. Can be of any supported type,
    :param value: value for the key,
    :param key_hint: (optional) Ignite data type, for which the given key
     should be converted,
    :param value_hint: (optional) Ignite data type, for which the given value
     should be converted.
    :param binary: pass True to keep the value in binary form. False
     by default,
    :param query_id: a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status and a boolean
     success code, or non-zero status and an error description if something
     has gone wrong.
    """

    class CacheReplaceQuery(Query):
        op_code = OP_CACHE_REPLACE

    query_struct = CacheReplaceQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('key', key_hint or AnyDataObject),
        ('value', value_hint or AnyDataObject),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'key': key,
        'value': value,
    })

    conn.send(send_buffer)

    response_struct = Response([
        ('success', Bool),
    ])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    if result.status != 0:
        return result
    result.value = response_struct.to_python(response)['success']
    return result


def cache_replace_if_equals(
    conn: Connection, cache: Union[str, int], key, sample, value,
    key_hint=None, sample_hint=None, value_hint=None,
    binary=False, query_id=None,
) -> APIResult:
    """
    Puts a value with a given key to cache only if the key already exists
    and value equals provided sample.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param key:  key for the cache entry,
    :param sample: a sample to compare the stored value with,
    :param value: new value for the given key,
    :param key_hint: (optional) Ignite data type, for which the given key
     should be converted,
    :param sample_hint: (optional) Ignite data type, for whic
     the given sample should be converted
    :param value_hint: (optional) Ignite data type, for which the given value
     should be converted,
    :param binary: (optional) pass True to keep the value in binary form.
     False by default,
    :param query_id: (optional) a value generated by client and returned
     as-is in response.query_id. When the parameter is omitted, a random
     value is generated,
    :return: API result data object. Contains zero status and a boolean
     success code, or non-zero status and an error description if something
     has gone wrong.
    """

    class CacheReplaceIfEqualsQuery(Query):
        op_code = OP_CACHE_REPLACE_IF_EQUALS

    query_struct = CacheReplaceIfEqualsQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('key', key_hint or AnyDataObject),
        ('sample', sample_hint or AnyDataObject),
        ('value', value_hint or AnyDataObject),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'key': key,
        'sample': sample,
        'value': value,
    })

    conn.send(send_buffer)

    response_struct = Response([
        ('success', Bool),
    ])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    if result.status != 0:
        return result
    result.value = response_struct.to_python(response)['success']
    return result


def cache_clear(
    conn: Connection, cache: Union[str, int], binary=False, query_id=None,
) -> APIResult:
    """
    Clears the cache without notifying listeners or cache writers.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param binary: (optional) pass True to keep the value in binary form.
     False by default,
    :param query_id: (optional) a value generated by client and returned
     as-is in response.query_id. When the parameter is omitted, a random
     value is generated,
    :return: API result data object. Contains zero status on success,
     non-zero status and an error description otherwise.
    """

    class CacheClearQuery(Query):
        op_code = OP_CACHE_CLEAR

    query_struct = CacheClearQuery([
        ('hash_code', Int),
        ('flag', Byte),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
    })
    conn.send(send_buffer)

    response_struct = Response([])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    return result


def cache_clear_key(
    conn: Connection, cache: Union[str, int], key,
    key_hint: object=None, binary=False, query_id=None,
) -> APIResult:
    """
    Clears the cache key without notifying listeners or cache writers.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param key:  key for the cache entry,
    :param key_hint: (optional) Ignite data type, for which the given key
     should be converted,
    :param binary: (optional) pass True to keep the value in binary form.
     False by default,
    :param query_id: (optional) a value generated by client and returned
     as-is in response.query_id. When the parameter is omitted, a random
     value is generated,
    :return: API result data object. Contains zero status on success,
     non-zero status and an error description otherwise.
    """

    class CacheClearKeyQuery(Query):
        op_code = OP_CACHE_CLEAR_KEY

    query_struct = CacheClearKeyQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('key', key_hint or AnyDataObject),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'key': key,
    })
    conn.send(send_buffer)

    response_struct = Response([])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    return result


def cache_clear_keys(
    conn: Connection, cache: Union[str, int], keys: list, binary=False, query_id=None,
) -> APIResult:
    """
    Clears the cache keys without notifying listeners or cache writers.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param keys: list of keys or tuples of (key, key_hint),
    :param binary: (optional) pass True to keep the value in binary form.
     False by default,
    :param query_id: (optional) a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status on success,
     non-zero status and an error description otherwise.
    """

    class CacheClearKeysQuery(Query):
        op_code = OP_CACHE_CLEAR_KEYS

    query_struct = CacheClearKeysQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('keys', AnyDataArray()),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'keys': keys,
    })
    conn.send(send_buffer)

    response_struct = Response([])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    return result


def cache_remove_key(
    conn: Connection, cache: Union[str, int], key,
    key_hint: object=None, binary=False, query_id=None,
) -> APIResult:
    """
    Clears the cache key without notifying listeners or cache writers.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param key:  key for the cache entry,
    :param key_hint: (optional) Ignite data type, for which the given key
     should be converted,
    :param binary: (optional) pass True to keep the value in binary form.
     False by default,
    :param query_id: (optional) a value generated by client and returned
     as-is in response.query_id. When the parameter is omitted, a random
     value is generated,
    :return: API result data object. Contains zero status and a boolean
     success code, or non-zero status and an error description if something
     has gone wrong.
    """

    class CacheRemoveKeyQuery(Query):
        op_code = OP_CACHE_REMOVE_KEY

    query_struct = CacheRemoveKeyQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('key', key_hint or AnyDataObject),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'key': key,
    })
    conn.send(send_buffer)

    response_struct = Response([
        ('success', Bool),
    ])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    if result.status != 0:
        return result
    result.value = response_struct.to_python(response)['success']
    return result


def cache_remove_if_equals(
    conn: Connection, cache: Union[str, int], key, sample,
    key_hint=None, sample_hint=None,
    binary=False, query_id=None,
) -> APIResult:
    """
    Removes an entry with a given key if provided value is equal to
    actual value, notifying listeners and cache writers.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param key:  key for the cache entry,
    :param sample: a sample to compare the stored value with,
    :param key_hint: (optional) Ignite data type, for which the given key
     should be converted,
    :param sample_hint: (optional) Ignite data type, for whic
     the given sample should be converted
    :param binary: (optional) pass True to keep the value in binary form.
     False by default,
    :param query_id: (optional) a value generated by client and returned
     as-is in response.query_id. When the parameter is omitted, a random
     value is generated,
    :return: API result data object. Contains zero status and a boolean
     success code, or non-zero status and an error description if something
     has gone wrong.
    """

    class CacheRemoveIfEqualsQuery(Query):
        op_code = OP_CACHE_REMOVE_IF_EQUALS

    query_struct = CacheRemoveIfEqualsQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('key', key_hint or AnyDataObject),
        ('sample', sample_hint or AnyDataObject),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'key': key,
        'sample': sample,
    })

    conn.send(send_buffer)

    response_struct = Response([
        ('success', Bool),
    ])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    if result.status != 0:
        return result
    result.value = response_struct.to_python(response)['success']
    return result


def cache_remove_keys(
    conn: Connection, cache: Union[str, int], keys: list, binary=False, query_id=None,
) -> APIResult:
    """
    Removes entries with given keys, notifying listeners and cache writers.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param keys: list of keys or tuples of (key, key_hint),
    :param binary: (optional) pass True to keep the value in binary form.
     False by default,
    :param query_id: (optional) a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status on success,
     non-zero status and an error description otherwise.
    """

    class CacheRemoveKeysQuery(Query):
        op_code = OP_CACHE_REMOVE_KEYS

    query_struct = CacheRemoveKeysQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('keys', AnyDataArray()),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'keys': keys,
    })
    conn.send(send_buffer)

    response_struct = Response([])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    return result


def cache_remove_all(
    conn: Connection, cache: Union[str, int], binary=False, query_id=None,
) -> APIResult:
    """
    Removes all entries from cache, notifying listeners and cache writers.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param binary: (optional) pass True to keep the value in binary form.
     False by default,
    :param query_id: (optional) a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status on success,
     non-zero status and an error description otherwise.
    """

    class CacheRemoveAllQuery(Query):
        op_code = OP_CACHE_REMOVE_ALL

    query_struct = CacheRemoveAllQuery([
        ('hash_code', Int),
        ('flag', Byte),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
    })
    conn.send(send_buffer)

    response_struct = Response([])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    return result


def cache_get_size(
    conn: Connection, cache: Union[str, int], peek_modes=0,
    binary=False, query_id=None,
) -> APIResult:
    """
    Gets the number of entries in cache.

    :param conn: connection to Ignite server,
    :param cache: name or ID of the cache,
    :param peek_modes: (optional) limit count to near cache partition
     (PeekModes.NEAR), primary cache (PeekModes.PRIMARY), or backup cache
     (PeekModes.BACKUP). Defaults to all cache partitions (PeekModes.ALL),
    :param binary: (optional) pass True to keep the value in binary form.
     False by default,
    :param query_id: (optional) a value generated by client and returned as-is
     in response.query_id. When the parameter is omitted, a random value
     is generated,
    :return: API result data object. Contains zero status and a number of
     cache entries on success, non-zero status and an error description
     otherwise.
    """
    if not isinstance(peek_modes, (list, tuple)):
        if peek_modes == 0:
            peek_modes = []
        else:
            peek_modes = [peek_modes]

    class CacheGetSizeQuery(Query):
        op_code = OP_CACHE_GET_SIZE

    query_struct = CacheGetSizeQuery([
        ('hash_code', Int),
        ('flag', Byte),
        ('peek_modes', PeekModes),
    ], query_id=query_id)

    _, send_buffer = query_struct.from_python({
        'hash_code': cache_id(cache),
        'flag': 1 if binary else 0,
        'peek_modes': peek_modes,
    })
    conn.send(send_buffer)

    response_struct = Response([
        ('count', Long),
    ])
    response_class, recv_buffer = response_struct.parse(conn)
    response = response_class.from_buffer_copy(recv_buffer)

    result = APIResult(response)
    if result.status != 0:
        return result
    result.value = response_struct.to_python(response)['count']
    return result
