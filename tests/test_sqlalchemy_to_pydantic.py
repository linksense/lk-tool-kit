#!/usr/bin/python3
# encoding: utf-8
# @Time    : 2022/1/6 16:13
# @author  : zza
# @Email   : 740713651@qq.com
# @File    : ${FILE_NAME}
import json
import os
from typing import List

from sqlalchemy import (
    DATETIME,
    Column,
    ForeignKey,
    Integer,
    String,
    create_engine,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker
from sqlalchemy.types import VARCHAR, TypeDecorator

from lk_tool_kit import sqlalchemy_to_pydantic

Base = declarative_base()

engine = create_engine("sqlite:///test_parse_operator.db", echo=True)


class JSONEncodedDict(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    nickname = Column(String)

    addresses = relationship(
        "Address", back_populates="user", cascade="all, delete, delete-orphan"
    )


class Address(Base):
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True)
    email_address = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="addresses")
    create_time = Column(DATETIME, nullable=False, server_default=func.now())
    ex_data = Column(JSONEncodedDict)


PydanticUser = sqlalchemy_to_pydantic(User)
PydanticAddress = sqlalchemy_to_pydantic(Address, exclude=["create_time"])


class PydanticUserWithAddresses(PydanticUser):
    addresses: List[PydanticAddress] = []

    class Config:
        orm_mode = True


Base.metadata.create_all(engine)

LocalSession = sessionmaker(bind=engine)

db: Session = LocalSession()


def setup_module():
    ed_user = User(name="ed", fullname="Ed Jones", nickname="edsnickname")
    address = Address(email_address="ed@example.com")
    address2 = Address(email_address="eddy@example.com")
    ed_user.addresses = [address, address2]
    db.add(ed_user)
    db.commit()


def teardown_module():
    if os.path.exists("sqlite:///test_parse_operator.db"):
        os.remove("sqlite:///test_parse_operator.db")


def test_pydantic_sqlalchemy():
    user = db.query(User).first()
    pydantic_user = PydanticUser.from_orm(user)
    data = pydantic_user.dict()
    assert data == {
        "fullname": "Ed Jones",
        "id": 1,
        "name": "ed",
        "nickname": "edsnickname",
    }
    pydantic_user_with_addresses = PydanticUserWithAddresses.from_orm(user)
    data = pydantic_user_with_addresses.dict()
    assert data == {
        "fullname": "Ed Jones",
        "id": 1,
        "name": "ed",
        "nickname": "edsnickname",
        "addresses": [
            {"email_address": "ed@example.com", "id": 1, "user_id": 1, "ex_data": None},
            {
                "email_address": "eddy@example.com",
                "id": 2,
                "user_id": 1,
                "ex_data": None,
            },
        ],
    }
