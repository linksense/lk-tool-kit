#!/usr/bin/python3
# encoding: utf-8
# @Time    : 2022/1/6 11:24
# @author  : zza
# @Email   : 740713651@qq.com
# @File    : ${FILE_NAME}
import os

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import BOOLEAN, FLOAT, INTEGER, VARCHAR, Column

from lk_tool_kit import parse_operator, parse_query_fields

# sqlalchemy
# Base = declarative_base()
# engine = create_engine("sqlite:///test_parse_operator.db")
# session = Session(engine)
# flask_sqlalchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test_parse_operator.db"
db = SQLAlchemy(app)


class DataModel(db.Model):
    __tablename__ = "data"
    obj_id: int = Column(INTEGER, primary_key=True)
    field_a: bool = Column(BOOLEAN)
    field_b: int = Column(INTEGER)
    field_c: str = Column(VARCHAR)
    x: float = Column(FLOAT)
    y: float = Column(FLOAT)


def teardown_module():
    if os.path.exists("sqlite:///test_parse_operator.db"):
        os.remove("sqlite:///test_parse_operator.db")


def test_parse_operator():
    query = db.session.query(DataModel)
    with pytest.raises(Exception):
        query.filter(parse_operator(DataModel.__table__, "field_d", "c"))

    with pytest.raises(Exception):
        query.filter(parse_operator(DataModel.__table__, "field_b__glt", 5))


def test_parse_query_fields():
    query_field = {
        "field_a": True,
        "field_b__gt": 20,
        "field_c__in": '["a", "b"]',
        "field_b__lt": 5,  # 1>b>5
        "or": [
            {"x__gt": 0, "y__gt": 0},  # x> 0 and y>0
            {"x__lt": 0, "y__lt": 0},  # x< 0 and y<0
        ],
    }
    query = db.session.query(DataModel)
    query = parse_query_fields(query, DataModel.__table__, query_field)
    sql_string = str(query.statement)

    _get_sql = """
    SELECT data.obj_id, data.field_a, data.field_b, data.field_c, data.x, data.y 
    FROM data 
    WHERE (data.field_a = :field_a_1) 
        AND (data.field_b > :field_b_1) 
        AND data.field_c IN (:field_c_1, :field_c_2) 
        AND (data.field_b < :field_b_2) 
        AND (((data.x > :x_1) AND (data.y > :y_1)) OR ((data.x < :x_2) AND (data.y < :y_2)))
      """
    for _str in _get_sql.split("\n"):
        assert _str.strip() in sql_string
