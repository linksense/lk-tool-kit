#!/usr/bin/python3
# encoding: utf-8
# @Time    : 2021/12/29 17:38
# @author  : zza
# @Email   : 740713651@qq.com
# @File    : operator_parse.py
import json
from typing import Type

from sqlalchemy.sql.elements import BinaryExpression
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
}


def parse_operator(
    class_obj: Table, key: str, value: str, exception_type: Type[Exception]
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
