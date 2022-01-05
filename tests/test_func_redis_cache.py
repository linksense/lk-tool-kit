#!/usr/bin/python3
# encoding: utf-8
# @Time    : 2022/1/4 11:13
# @author  : zza
# @Email   : 740713651@qq.com
# @File    : test_func_redis_cache.py
import datetime
import time
from typing import Optional

import pytest

from lk_tool_kit import RedisCache


def _get_time_str(timestamp: int = None) -> Optional[str]:
    if timestamp is None:
        return datetime.datetime.now().isoformat()
    if timestamp <= 50:
        return None
    return datetime.datetime.fromtimestamp(timestamp).isoformat()


async def _async_get_datetime(timestamp: int = None) -> datetime.datetime:
    if timestamp is None:
        return datetime.datetime.now()
    return datetime.datetime.fromtimestamp(timestamp)


async def async_get_time_str(timestamp: int = None) -> str:
    return _get_time_str(timestamp)


class TestRedisCache:
    r_cache: RedisCache

    @classmethod
    def setup_class(cls):
        cls.r_cache = RedisCache.from_url("redis://127.0.0.1:6379/1", debug=True)

    def setup_method(self):
        self.r_cache.delete_all()

    def test_cached(self):
        _get_time = self.r_cache.cached(metrics=True)(_get_time_str)
        _get_time.bust_all()
        tmp_str = _get_time()  # miss+1
        assert tmp_str == _get_time()
        _get_time.bust()
        assert tmp_str != _get_time()  # miss+1

        assert _get_time.metrics["misses"] == 2

        assert len(_get_time.redis_keys()) == 1
        assert self.r_cache.unmake_key(_get_time.redis_keys()[0]).startswith(
            _get_time.__name__
        )

        _get_time(1)
        assert len(_get_time.redis_keys()) == 2

    @pytest.mark.asyncio
    async def test_async_cached(self):
        _get_datetime = self.r_cache.cached(metrics=True)(_async_get_datetime)
        now = await _get_datetime()  # miss+1
        assert now == await _get_datetime()  # hit +1
        _get_datetime.bust()

    def test_none_response(self):
        _get_time = self.r_cache.cached(metrics=True)(_get_time_str)
        _get_time.bust_all()
        _get_time(1)
        _get_time(1)
        assert _get_time.metrics["misses"] == 1
        assert _get_time.metrics["hits"] == 1

    def test_timeout_response(self):
        _get_time = self.r_cache.cached(metrics=True, timeout=1)(_get_time_str)
        _get_time.bust_all()
        _get_time(1)
        time.sleep(1)
        _get_time(1)
        assert _get_time.metrics["misses"] == 2
