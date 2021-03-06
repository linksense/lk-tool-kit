#!/usr/bin/python3
# encoding: utf-8
# @Time    : 2021/12/29 17:55
# @author  : zza
# @Email   : 740713651@qq.com
# @File    : pymysql_converters_update.py
from typing import Any, Optional

import numpy
import pandas
import pymysql


def _escape_pd_timestamp(obj: pandas.Timestamp, mapping: Optional[Any] = None) -> str:
    """
    将pandas.Timestamp 转换为datetime

    >>> _escape_pd_timestamp(pandas.Timestamp(0))
    "'1970-01-01'"
    """
    return pymysql.converters.escape_date(obj.to_pydatetime(), mapping)


def pymysql_converters_update() -> None:
    """
    pymysql不支持numpy的部分类型

    >>> pymysql_converters_update()
    """

    pymysql.converters.encoders[pandas.Timestamp] = _escape_pd_timestamp
    pymysql.converters.encoders[numpy.float64] = pymysql.converters.escape_float
    pymysql.converters.encoders[numpy.int64] = pymysql.converters.escape_int
    pymysql.converters.conversions = pymysql.converters.encoders.copy()
    pymysql.converters.conversions.update(pymysql.converters.decoders)
