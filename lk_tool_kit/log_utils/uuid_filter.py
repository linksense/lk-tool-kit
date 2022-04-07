#!/usr/bin/python3
# encoding: utf-8
# @Time    : 2021/12/29 17:32
# @author  : zza
# @Email   : 740713651@qq.com
# @File    : uuid_filter.py
import logging
import uuid


class UUIDFilter(logging.Filter):
    def __init__(self, name: str = "", uuid_str: str = None):
        """uuid 日志工具

        在打印的日志中，增加uuid显示（如果LOG_FORMAT中存在 %(uuid)s ）

        Args:
            name:
            uuid_str:

        >>> base_handler = logging.StreamHandler()
        >>> uuid_filter = UUIDFilter(uuid_str="Server")
        >>> base_handler.addFilter(uuid_filter)
        """
        super(UUIDFilter, self).__init__(name)
        self.uuid = uuid_str or str(uuid.uuid4().hex)

    def filter(  # noqa: A003
        self, log_record: logging.LogRecord
    ) -> bool:  # pragma: no cover
        """设置日志中的uuid的值"""
        log_record.uuid = self.uuid
        return True

    def set_uuid(self, uuid_str: str) -> None:
        """设置
        >>> UUIDFilter("tmp").set_uuid(None)
        """
        if not uuid_str:
            uuid_str = str(uuid.uuid4().hex)
        self.uuid = uuid_str
