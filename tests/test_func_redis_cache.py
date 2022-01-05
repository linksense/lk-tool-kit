#!/usr/bin/python3
# encoding: utf-8
# @Time    : 2022/1/4 11:13
# @author  : zza
# @Email   : 740713651@qq.com
# @File    : test_func_redis_cache.py
import datetime

from lk_tool_kit import RedisCache


def get_time_str(timestamp: int = None) -> str:
    if timestamp is None:
        return datetime.datetime.now().isoformat()
    return datetime.datetime.fromtimestamp(timestamp).isoformat()


async def async_get_time_str(timestamp: int = None) -> str:
    return get_time_str(timestamp)


class TestRedisCache:
    r_cache: RedisCache

    @classmethod
    def setup_class(cls):
        cls.r_cache = RedisCache.from_url("redis://127.0.0.1:6379/1", debug=True)
        cls.r_cache.delete_all()

    def test_cached(self):
        _get_time_str = self.r_cache.cached(metrics=True)(get_time_str)
        _get_time_str.bust_all()
        tmp_str = _get_time_str()  # miss+1
        assert tmp_str == _get_time_str()
        _get_time_str.bust()
        assert tmp_str != _get_time_str()  # miss+1

        assert _get_time_str.metrics["misses"] == 2

        # self.r_cache.cached(async_get_time_str)
