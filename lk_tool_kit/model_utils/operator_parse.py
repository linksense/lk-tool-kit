#!/usr/bin/python3
# encoding: utf-8
# @Time    : 2021/12/29 17:38
# @author  : zza
# @Email   : 740713651@qq.com
# @File    : operator_parse.py
import json
from typing import Any, Dict, Type, Union

from sqlalchemy import and_, or_, tuple_
from sqlalchemy.orm import Query
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList
from sqlalchemy.sql.schema import Table

# 参考mongo写的 https://docs.mongodb.com/manual/reference/operator/query-comparison/
_operator_map = {
    None: lambda attr, v: attr.op("=")(v),  # k:v - k=v
    "eq": lambda attr, v: attr.op("=")(v),  # k__eq:v - k=v
    "gt": lambda attr, v: attr.op(">")(v),  # k__gt:v - k>v
    "gte": lambda attr, v: attr.op(">=")(v),  # k__gte:v - k>=v
    "in": lambda attr, v: attr.in_(json.loads(v)),  # k__in:v - k in v
    "lt": lambda attr, v: attr.op("<")(v),  # k__lt:v - k<v
    "lte": lambda attr, v: attr.op("<=")(v),  # k__lte:v - k<=v
    "ne": lambda attr, v: attr.op("!=")(v),  # k__ne:v - k!=v
    "nin": lambda attr, v: attr.notin_(json.loads(v)),  # k__nin:v k not in v
    "regex": lambda attr, v: attr.like("%{}%".format(v)),  # k__regex:v k contains v
    # "or":  _get_query 支持用 or 做查询 逻辑与操作符逻辑不通
}


def parse_operator(
    class_obj: Table,
    key: str,
    value: Union[str, int],
    exception_type: Type[Exception] = Exception,
) -> BinaryExpression:
    """将查询请求转换mysql识别的 BinaryExpression
    eg。 x__gt:30 -> filter(x >= 30 )
    eg。 x__in:[1,2,3] -> filter(x.in_([1,2,3]))
    """
    if "__" in key:
        attr_name, _operator = key.split("__")
    else:
        _operator = None
        attr_name = key
    attr = class_obj.columns.get(attr_name)
    if attr is None:
        raise exception_type("未知字段{}".format(attr_name))
    if _operator not in _operator_map.keys():
        raise exception_type("未知操作符{}".format(key))
    return _operator_map[_operator](attr, value)


def _get_query(
    table: Table,
    query_field: Dict[str, Union[str, int, Dict[str, Any]]],
    exception_type: Type[Exception] = Exception,
) -> BooleanClauseList:
    """解析查询语气"""
    sub_query_list = []
    for field, value in query_field.items():
        if field == "or":
            # or 多重条件查询 需要考虑递归情况
            # value =[{"x__gt": 20, "x": 10}]
            _sub_query_list = []
            for _query_field in value:
                _or_query = _get_query(
                    table=table,
                    query_field=_query_field,
                    exception_type=exception_type,
                )
                # 默认 and 不会有最外层括号 需要用 tuple 包裹
                _sub_query_list.append(tuple_(_or_query))
            _query = or_(*_sub_query_list)
        else:
            # 正常操作符 走 parse_operator 逻辑
            _query = parse_operator(table, field, value, exception_type=exception_type)
        sub_query_list.append(_query)
    final_query = and_(*sub_query_list)
    return final_query


def parse_query_fields(
    query: Query,
    table: Table,
    query_field: Dict[str, Union[str, int, Dict[str, Any]]],
    exception_type: Type[Exception] = Exception,
) -> Query:
    """转化字段查询未sqlalchemy查询

    Args:
        query: sqlalchemy.query
        table: 表对象
        query_field: 查询字典(json)
        exception_type: 出错时的异常类型

    Returns:
         sqlalchemy.query 对象

    案例详见单元测试 tests.test_operator_parse.test_parse_query_fields
    """
    final_query = _get_query(table, query_field, exception_type)
    query = query.filter(final_query)
    return query
