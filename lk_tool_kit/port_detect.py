#!/usr/bin/python3
# encoding: utf-8 
# @Time    : 2022/1/7 16:19
# @author  : zza
# @Email   : 740713651@qq.com
# @File    : port_detect.py
import socket
from typing import Union


def port_used(ip: str = "127.0.0.1", port: Union[int, str] = "80") -> bool:
    """ 检测端口是否被占用

    Returns:
        bool

    >>> port_used("127.0.0.1",22)
    True
    >>> port_used("127.0.0.1",55551)
    False
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        return True
    except OSError:
        return False
    finally:
        s.close()
