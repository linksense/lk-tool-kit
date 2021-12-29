#!/usr/bin/python3
# encoding: utf-8
# @Time    : 2021/12/29 17:55
# @author  : zza
# @Email   : 740713651@qq.com
# @File    : pymysql_converters_update.py
import numpy
import pandas
import pymysql


def pymysql_converters_update():
    """pymysql不支持numpy的部分类型"""

    def escape_pd_timestamp(obj, mapping=None):
        """将pandas.Timestamp 转换为datetime"""
        return pymysql.converters.escape_date(obj.to_pydatetime(), mapping)

    pymysql.converters.encoders[pandas.Timestamp] = escape_pd_timestamp
    pymysql.converters.encoders[numpy.float64] = pymysql.converters.escape_float
    pymysql.converters.encoders[numpy.int64] = pymysql.converters.escape_int
    pymysql.converters.conversions = pymysql.converters.encoders.copy()
    pymysql.converters.conversions.update(pymysql.converters.decoders)
