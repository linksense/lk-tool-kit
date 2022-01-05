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
import inspect
import pickle  # noqa: S403
import time
from functools import wraps
from typing import Any, Callable, Iterable, Optional, TypeVar

import redis

RT = TypeVar("RT")  # return type


def _key_fn(*args, **kwargs) -> str:
    """Generating function parameter signatures"""
    return hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()  # noqa: S303


class RedisCache(object):
    def __init__(
        self,
        database: redis.Redis = None,
        name: str = "cache",
        default_timeout: int = None,
        debug: bool = False,
    ):
        """基于redis的函数缓存工具

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

    @classmethod
    def from_url(
        cls,
        url: str,
        name: str = "cache",
        default_timeout: int = None,
        debug: bool = False,
    ) -> "RedisCache":
        """通过redis url创建Redis Cache

        Args:
            url: redis url eg."redis://localhost:6379/1"
            name: Namespace for this cache.
            default_timeout: Default cache timeout.
            debug: Disable cache for debugging purposes. Cache will no-op.

        Returns:
            RedisCache
        """
        r_db = redis.from_url(url)
        func_cache = cls(
            database=r_db,
            name=name,
            default_timeout=default_timeout,
            debug=debug,
        )
        return func_cache

    def make_key(self, string: str) -> str:
        """生成redis key"""
        return ":".join((self.name, string))

    def unmake_key(self, key: str) -> str:
        """还原redis key至函数签名"""
        return key[self.prefix_len :]  # noqa: E203

    def delete(self, key: str) -> int:
        """删除缓存"""
        return self.database.delete(self.make_key(key))

    def delete_all(self, key: str = "*") -> int:
        """删除全部缓存

        Args:
            key: 函数名 默认为全部函数

        Returns:
            删除条目

        默认删除RedisCache生成的全部函数缓存
            redis中,以RedisCache.name开头的函数 `name:*`
        """
        keys = [key.decode() for key in self.database.keys(self.make_key(key))]
        if not keys:
            return 0
        return self.database.delete(*keys)

    def keys(self, key: str = "*") -> Iterable[str]:
        """获取所有缓存

        默认RedisCache的所有缓存
        """
        keys = [key.decode() for key in self.database.keys(self.make_key(key))]
        return keys

    def get(self, key: str, default: Any = None) -> Any:
        key = self.make_key(key)
        value = self.database.get(key)
        if not value:
            self.metrics["misses"] += 1
            return default
        else:
            self.metrics["hits"] += 1
            return pickle.loads(value)  # noqa: S301

    def set_response(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:

        key = self.make_key(key)
        pickled_value = pickle.dumps(value)
        self.metrics["writes"] += 1
        if timeout:
            return self.database.setex(key, int(timeout), pickled_value)
        else:
            return self.database.set(key, pickled_value)

    def cached(
        self,
        key_fn: Callable[..., str] = _key_fn,
        timeout: int = None,
        metrics: bool = False,
    ) -> Callable[[Callable[..., RT]], Callable[..., RT]]:
        """缓存函数

        Args:
            key_fn: redis中的缓存名获取器 默认md5
            timeout: 缓存过期时间 优先级大于RedisCache
            metrics: 是否开启计数指标
        """
        if timeout is None:
            timeout = self.default_timeout

        def decorator(func: Callable[..., RT]) -> Callable[..., RT]:
            def make_key(*args, **kwargs) -> str:
                return "%s:%s" % (func.__name__, key_fn(*args, **kwargs))

            def bust(*args, **kwargs) -> int:
                """删除对应缓存"""
                key = make_key(*args, **kwargs)
                return self.delete(key)

            def bust_all() -> int:
                """删除该函数所有缓存"""
                key = "%s:*" % func.__name__
                return self.delete_all(key)

            def redis_keys() -> Iterable[str]:
                key = "%s:*" % func.__name__
                return self.keys(key)

            _metrics = {"hits": 0, "misses": 0, "avg_hit_time": 0, "avg_miss_time": 0}
            if inspect.iscoroutinefunction(func):

                @wraps(func)
                async def inner(*args, **kwargs) -> RT:
                    start = time.time()
                    is_cache_hit = True
                    key = make_key(args, kwargs)
                    res = self.get(key)
                    if res is None:
                        res = await func(*args, **kwargs)
                        self.set_response(key, res, timeout)
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

            else:

                @wraps(func)
                def inner(*args, **kwargs) -> RT:
                    start = time.time()
                    is_cache_hit = True
                    key = make_key(*args, **kwargs)
                    res = self.get(key)
                    if res is None:
                        res = func(*args, **kwargs)
                        self.set_response(key, res, timeout)
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
            inner.redis_keys = redis_keys
            if metrics:
                inner.metrics = _metrics
            return inner

        return decorator
