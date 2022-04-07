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
from typing import Any, Callable, List, Optional, TypeVar, Union

import redis

from lk_tool_kit.mixins import Serializable

RT = TypeVar("RT")  # return type


def _key_fn(*args, **kwargs) -> str:
    """Generating function parameter signatures"""
    return hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()  # noqa: S303


class NoneCache:
    """无返回值时返回的对象 用于区别None"""


class RedisCacheValue(Serializable):
    def __init__(self, value: Any):
        self.value = value

    @classmethod
    def is_legacy_version(cls, data: bytes) -> bool:
        return False


class FunctionDecorator:
    def __init__(
        self,
        func: Callable[..., RT],
        redis_cache: "RedisCache",
        key_fn: Callable[..., str] = _key_fn,
        timeout: int = None,
        metrics_enabled: bool = False,
        compress: bool = False,
    ):
        self.func = func
        self.key_fn = key_fn
        self.timeout = timeout
        self.metrics_enabled = metrics_enabled
        self.redis_cache = redis_cache
        self.metrics = {"hits": 0, "misses": 0, "avg_hit_time": 0, "avg_miss_time": 0}
        self.compress = compress
        wraps(func)(self)

    def make_key(self, *args, **kwargs) -> str:
        return "%s:%s" % (self.func.__name__, self.key_fn(*args, **kwargs))

    def bust(self, *args, **kwargs) -> int:
        """删除对应缓存"""
        key = self.make_key(*args, **kwargs)
        return self.redis_cache.delete(key)

    def bust_all(self) -> int:
        """删除该函数所有缓存"""
        key = "%s:*" % self.func.__name__
        return self.redis_cache.delete_all(key)

    def redis_keys(self) -> List[str]:
        key = "%s:*" % self.func.__name__
        return self.redis_cache.keys(key)

    def _record_metrics(self, is_cache_hit: bool, start: float) -> None:
        if self.metrics_enabled:
            dur = time.time() - start
            if is_cache_hit:
                self.metrics["hits"] += 1
                self.metrics["avg_hit_time"] += dur / self.metrics["hits"]
            else:
                self.metrics["misses"] += 1
                self.metrics["avg_miss_time"] += dur / self.metrics["misses"]

    def __call__(self, *args, **kwargs) -> RT:
        start = time.time()
        is_cache_hit = True
        key = self.make_key(*args, **kwargs)
        res = self.redis_cache.get(key)
        if res is NoneCache:
            res: Any = self.func(*args, **kwargs)
            res: RedisCacheValue = RedisCacheValue(res)
            bytes_data: bytes = RedisCacheValue.serialize(
                time.time(), res, compress=self.compress
            )
            self.redis_cache.set_response(key, bytes_data, self.timeout)
            is_cache_hit = False
        else:
            res: RedisCacheValue = RedisCacheValue.deserialize(
                res, compress=self.compress
            )

        self._record_metrics(is_cache_hit, start)
        return res.value


class AsyncFunctionDecorator(FunctionDecorator):
    async def __call__(self, *args, **kwargs) -> RT:
        start = time.time()
        is_cache_hit = True
        key = self.make_key(*args, **kwargs)
        res = self.redis_cache.get(key)
        if res is NoneCache:
            res: Any = await self.func(*args, **kwargs)
            res: RedisCacheValue = RedisCacheValue(res)
            bytes_data: bytes = RedisCacheValue.serialize(
                time.time(), res, compress=self.compress
            )
            self.redis_cache.set_response(key, bytes_data, self.timeout)
            is_cache_hit = False
        else:
            res: RedisCacheValue = RedisCacheValue.deserialize(
                res, compress=self.compress
            )

        self._record_metrics(is_cache_hit, start)
        return res.value


class RedisCache(object):
    def __init__(
        self,
        database: redis.Redis = None,
        name: str = "cache",
        default_timeout: int = None,
        debug: bool = False,
        compress: bool = False,
    ):
        """基于redis的函数缓存工具

        Args:
            database: py:class:`Database` instance.
            name: Namespace for this cache.
            default_timeout: Default cache timeout.
            debug: Disable cache for debugging purposes. Cache will no-op.
            compress: Compress cache values using zlib.

        >>> r_cache = RedisCache.from_url("redis://localhost:6379")
        >>> @r_cache.cached(timeout=3, metrics=True, compress=True)
        ... def get_obj_str(string: int = None) -> Optional[str]:
        ...     if string is None:
        ...         return "no obj"
        ...     return str(string)
        >>>
        >>> assert get_obj_str(10) == get_obj_str(10) # 使用缓存 结果一样
        >>> assert get_obj_str.metrics["misses"] == 1 # 第一次无缓存
        >>> assert get_obj_str.metrics["hits"] == 1 # 第二次命中缓存
        >>> assert get_obj_str.bust(10) == 1 # 删除特定参数的缓存
        >>> assert get_obj_str.bust_all() == 0 # 删除所有缓存
        >>> @r_cache.cached(timeout=3, metrics=True)
        ... def get_obj_str_wo_compress(string: int = None) -> Optional[str]:
        ...     if string is None:
        ...         return "no obj"
        ...     return str(string)
        >>>
        >>> assert get_obj_str_wo_compress(10) == get_obj_str(10) # 使用缓存 结果一样
        >>> assert get_obj_str_wo_compress(10) == get_obj_str(10) # 使用缓存 结果一样
        >>> assert get_obj_str_wo_compress.metrics["misses"] == 1 # 第一次无缓存
        >>> assert get_obj_str_wo_compress.metrics["hits"] == 1 # 第二次命中缓存
        >>> assert get_obj_str_wo_compress.bust(10) == 1 # 删除特定参数的缓存
        >>> assert get_obj_str_wo_compress.bust_all() == 0 # 删除所有缓存
        """
        self.database = database
        self.name = name
        self.prefix_len = len(self.name) + 1
        self.default_timeout = default_timeout
        self.metrics = {"hits": 0, "misses": 0, "writes": 0}
        self.debug = debug
        self.compress = compress

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

    def keys(self, key: str = "*") -> List[str]:
        """获取所有缓存

        默认RedisCache的所有缓存
        """
        keys = [key.decode() for key in self.database.keys(self.make_key(key))]
        return keys

    def get(self, key: str, default: Any = NoneCache) -> Any:
        key = self.make_key(key)
        value = self.database.get(key)
        if not value:
            self.metrics["misses"] += 1
            return default
        else:
            self.metrics["hits"] += 1
            return value

    def set_response(
        self, key: str, value: bytes, timeout: Optional[int] = None
    ) -> bool:
        key = self.make_key(key)
        self.metrics["writes"] += 1
        if timeout:
            return self.database.setex(key, int(timeout), value)
        else:
            return self.database.set(key, value)

    def cached(
        self,
        key_fn: Callable[..., str] = _key_fn,
        timeout: int = None,
        metrics: bool = False,
        compress: bool = None,
    ) -> Callable[
        [Callable[..., RT]],
        Union[Callable[..., RT], AsyncFunctionDecorator, FunctionDecorator],
    ]:
        """缓存函数

        Args:
            key_fn: redis中的缓存名获取器 默认md5
            timeout: 缓存过期时间 优先级大于RedisCache
            metrics: 是否开启计数指标
        """
        if timeout is None:
            timeout = self.default_timeout
        if compress is None:
            compress = self.compress

        def decorator(
            func: Callable[..., RT]
        ) -> Union[Callable[..., RT], AsyncFunctionDecorator, FunctionDecorator]:

            if inspect.iscoroutinefunction(func):
                inner = AsyncFunctionDecorator(
                    func, self, key_fn, timeout, metrics, compress
                )

            else:
                inner = FunctionDecorator(
                    func, self, key_fn, timeout, metrics, compress
                )

            return inner

        return decorator


__all__ = [RedisCache]
