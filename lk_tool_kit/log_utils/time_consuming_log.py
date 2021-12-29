#!/usr/bin/python3
# encoding: utf-8
# @Time    : 2021/12/29 18:23
# @author  : zza
# @Email   : 740713651@qq.com
# @File    : time_consuming_log.py

import functools
import inspect
import logging
import time
from typing import Any, Callable, Dict, Iterable


def time_consuming_log(
    logger: logging.Logger, log_level: int = logging.INFO
) -> Callable:
    """
    耗时日志装饰器

    Args:
        logger: logger类型
        log_level: logger级别
    """

    def before_call(
        func: Callable, args: Iterable[Any], kwargs: Dict[Any, Any]
    ) -> float:
        bound_values = inspect.signature(func).bind(*args, **kwargs)
        start_log = "[Func {}]: {}(**{})".format(
            func.__name__, func.__name__, dict(bound_values.arguments)
        )
        logger.log(log_level, start_log)
        start_time = time.time()
        return start_time

    def after_call(func: Callable, start_time: time.time, ret: Any) -> None:
        used_time = round(time.time() - start_time, 6)
        end_log = "[Func {}](finish in {}s) return: {}".format(
            func.__name__, used_time, ret
        )
        logger.log(log_level, end_log)

    def middle_wrapper(func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                start_time = before_call(func, args, kwargs)
                ret = await func(*args, **kwargs)
                after_call(func, start_time, ret)
                return ret

            return wrapper
        else:

            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                start_time = before_call(func, args, kwargs)
                ret = func(*args, **kwargs)
                after_call(func, start_time, ret)
                return ret

            return wrapper

    return middle_wrapper


@functools.lru_cache(1)
def get_true(flag: bool = True) -> bool:
    """
    >>> get_true()
    True
    """
    return flag
