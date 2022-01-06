#!/usr/bin/python3
# encoding: utf-8
# @Time    : 2022/1/6 10:20
# @author  : zza
# @Email   : 740713651@qq.com
# @File    : test_func_redis_cache.py
import logging

import pytest

from lk_tool_kit import time_consuming_log


@pytest.mark.asyncio
async def test_async_consuming_log():
    log = logging.getLogger("tmp")

    @time_consuming_log(log, logging.DEBUG)
    async def _inner_print_func(*args, **kwargs) -> None:
        print(*args, **kwargs)

    await _inner_print_func(2503)
