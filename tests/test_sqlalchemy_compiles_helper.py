#!/usr/bin/python3
# encoding: utf-8
# @Time    : 2022/1/10 11:51
# @author  : zza
# @Email   : 740713651@qq.com
# @File    : ${FILE_NAME}

from sqlalchemy import (
    INTEGER,
    Column,
    Integer,
    PrimaryKeyConstraint,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base

from lk_tool_kit import compiles_init

Base = declarative_base()

engine = create_engine(
    "mysql+pymysql://root:P%40ss1234@192.168.0.122/tmp_db?charset=utf8", echo=True
)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        PrimaryKeyConstraint(
            "id",
            "avi_id",
        ),
        dict(
            mysql_engine="InnoDB",
            mysql_partition_by="LIST COLUMNS(avi_id)",
            mysql_partitions=["0"],
        ),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64))
    avi_id = Column(INTEGER)


def _drop_table():
    if User.__table__.exists(engine):
        User.__table__.drop(engine)


def setup_module():
    _drop_table()
    compiles_init()


def teardown_module():
    _drop_table()


def test_add_partition_scheme():
    User.__table__.create(engine)
    assert User.__table__.exists(engine)
