#!/usr/bin/python3
# encoding: utf-8
# @Time    : 2021/11/25 14:41
# @author  : zza
# @Email   : 740713651@qq.com
# @File    : cache.py
"""
copy from https://github.com/accaolei/func_cache/blob/master/func_cache/cache.py
"""
import hashlib
import pickle
import time
from functools import wraps
from typing import Callable


def _key_fn(a, k):
    return hashlib.md5(pickle.dumps((a, k))).hexdigest()


class RedisCache(object):
    def __init__(
        self,
        database=None,
        name: str = "cache",
        default_timeout: int = None,
        debug: bool = False,
    ):
        """ 基于redis的函数缓存工具

        Args:
            database: py:class:`Database` instance.
            name: Namespace for this cache.
            default_timeout: Default cache timeout.
            debug: Disable cache for debugging purposes. Cache will no-op.
        """
        self.database = database
        self.name = name
        self.prefix_len = len(self.name) + 1
        self.default_timeout = default_timeout
        self.metrics = {"hits": 0, "misses": 0, "writes": 0}
        self.debug = debug

    def make_key(self, s):
        return ":".join((self.name, s))

    def unmake_key(self, k):
        return k[self.prefix_len:]

    def delete(self, key):
        if self.debug:
            return 0
        return self.database.delete(self.make_key(key))

    def get(self, key, default=None):
        key = self.make_key(key)

        if self.debug:
            return default

        value = self.database.get(key)
        if not value:
            self.metrics["misses"] += 1
            return default
        else:
            self.metrics["hits"] += 1
            return pickle.loads(value)

    def set(self, key, value, timeout=None):

        key = self.make_key(key)

        if self.debug:
            return True

        pickled_value = pickle.dumps(value)
        self.metrics["writes"] += 1
        if timeout:
            return self.database.setex(key, int(timeout), pickled_value)
        else:
            return self.database.set(key, pickled_value)

    def cached(self, key_fn=_key_fn, timeout=None, metrics=False) -> Callable:
        """ 缓存函数

        Args:
            key_fn: redis中的缓存名获取器 默认md5
            timeout: 缓存过期时间
            metrics: 是否开启计数指标

        Returns:

        """

        def decorator(fn: Callable):
            def make_key(args, kwargs):
                return "%s:%s" % (fn.__name__, key_fn(args, kwargs))

            def bust(*args, **kwargs):
                """删除对应缓存"""
                key = make_key(args, kwargs)
                return self.delete(key)

            def bust_all():
                """删除该函数所有缓存"""
                key = "%s:*" % fn.__name__
                return self.delete(key)

            _metrics = {"hits": 0, "misses": 0, "avg_hit_time": 0, "avg_miss_time": 0}

            @wraps(fn)
            def inner(*args, **kwargs):
                start = time.time()
                is_cache_hit = True
                key = make_key(args, kwargs)
                res = self.get(key)
                if res is None:
                    res = fn(*args, **kwargs)
                    self.set(key, res, timeout)
                    is_cache_hit = False

                if metrics:
                    dur = time.time() - start
                    if is_cache_hit:
                        _metrics["hits"] += 1
                        _metrics["avg_hit_time"] += dur / _metrics["hits"]
                    else:
                        _metrics["misses"] += 1
                        _metrics["avg_miss_time"] += dur / _metrics["misses"]

                return res

            inner.bust = bust
            inner.bust_all = bust_all
            inner.make_key = make_key
            if metrics:
                inner.metrics = _metrics
            return inner

        return decorator

    def async_cached(self, key_fn=_key_fn, timeout=None, metrics=False):
        def decorator(fn):
            def make_key(args, kwargs):
                return "%s:%s" % (fn.__name__, key_fn(args, kwargs))

            def bust(*args, **kwargs):
                return self.delete(make_key(args, kwargs))

            _metrics = {"hits": 0, "misses": 0, "avg_hit_time": 0, "avg_miss_time": 0}

            @wraps(fn)
            async def inner(*args, **kwargs):
                start = time.time()
                is_cache_hit = True
                key = make_key(args, kwargs)
                res = self.get(key)
                if res is None:
                    res = await fn(*args, **kwargs)
                    self.set(key, res, timeout)
                    is_cache_hit = False

                if metrics:
                    dur = time.time() - start
                    if is_cache_hit:
                        _metrics["hits"] += 1
                        _metrics["avg_hit_time"] += dur / _metrics["hits"]
                    else:
                        _metrics["misses"] += 1
                        _metrics["avg_miss_time"] += dur / _metrics["misses"]

                return res

            inner.bust = bust
            inner.make_key = make_key
            if metrics:
                inner.metrics = _metrics
            return inner

        return decorator

    def cached_property(self, key_fn=_key_fn, timeout=None, _async=False):
        this = self

        class _cached_property(object):
            def __init__(self, fn):
                if _async:
                    self._fn = this.async_cached(key_fn, timeout)(fn)
                else:
                    self._fn = this.cached(key_fn, timeout)(fn)

            def __get__(self, instance, instance_type=None):
                if instance is None:
                    return self
                return self._fn(instance)

            def __delete__(self, obj):
                self._fn.bust(obj)

            def __set__(self, instance, value):
                raise ValueError("Cannot set value of a cached property.")

        def decorator(fn):
            return _cached_property(fn)

        return decorator
