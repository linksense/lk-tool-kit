#!/usr/bin/python3
# encoding: utf-8
# @Time    : 2022/1/10 11:20
# @author  : zza
# @Email   : 740713651@qq.com
# @File    : sqlalchemy_compiles_helper.py
from typing import Callable, List

from sqlalchemy.dialects.mysql.base import MySQLDDLCompiler
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import CreateTable


@compiles(CreateTable, "mysql")
def add_partition_scheme(element: CreateTable, compiler: MySQLDDLCompiler) -> str:
    """增加分区字段解析

    __table_args__ 中增加
        mysql_partition_by: 分区字段 eg. "LIST COLUMNS(avi_id)"
        mysql_partitions: 分区值 eg. ["0"]

    样例请见单元测试 tests/test_sqlalchemy_compiles_helper.py
    """
    table = element.element
    partition_by = table.kwargs.pop("mysql_partition_by", None)
    partitions = table.kwargs.pop("mysql_partitions", None)

    ddl = compiler.visit_create_table(element)
    ddl = ddl.rstrip()

    if partition_by:
        ddl += "\nPARTITION BY %s" % partition_by
        table.kwargs["mysql_partition_by"] = partition_by
    if partitions:
        _sql = []
        for par_code in partitions:
            _sql.append("PARTITION p_{} VALUES IN({}) ".format(par_code.replace("'", ""), par_code))
        ddl += "({})".format(", ".join(_sql))
        table.kwargs["mysql_partitions"] = partitions

    return ddl


def compiles_init() -> List[Callable]:
    """需要import此文件将 compiles加载到sqlalchemy框架中"""
    _all = [add_partition_scheme]
    return _all
