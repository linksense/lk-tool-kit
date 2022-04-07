#!/usr/bin/python3
# encoding: utf-8
# @Time    : 2021/12/29 17:45
# @author  : zza
# @Email   : 740713651@qq.com
# @File    : sqlalchemy_to_pydantic.py
"""
copy from https://github.com/tiangolo/pydantic-sqlalchemy
source noe support sqlalchemy == 1.3.10
"""
from typing import Container, Optional, Type

from pydantic import BaseConfig, BaseModel, create_model
from sqlalchemy.inspection import inspect as sqlalchemy_inspect
from sqlalchemy.orm.properties import ColumnProperty


class OrmConfig(BaseConfig):
    orm_mode = True


def sqlalchemy_to_pydantic(
    db_model: Type, *, config: Type = OrmConfig, exclude: Container[str] = None
) -> Type[BaseModel]:
    if exclude is None:
        exclude = []
    mapper = sqlalchemy_inspect(db_model)
    fields = {}
    for attr in mapper.attrs:
        if isinstance(attr, ColumnProperty):
            if attr.columns:
                name = attr.key
                if name in exclude:
                    continue
                column = attr.columns[0]
                python_type: Optional[type] = None
                if hasattr(column.type, "impl"):
                    if hasattr(column.type.impl, "python_type"):
                        python_type = column.type.impl.python_type
                elif hasattr(column.type, "python_type"):
                    python_type = column.type.python_type
                assert (  # noqa: S101
                    python_type
                ), f"Could not infer python_type for {column}"
                default = None
                if column.default is None and not column.nullable:
                    default = ...
                fields[name] = (python_type, default)
    pydantic_model = create_model(
        db_model.__name__, __config__=config, **fields  # type: ignore
    )
    return pydantic_model
