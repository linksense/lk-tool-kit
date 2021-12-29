#!/usr/bin/python3
# encoding: utf-8
# @Time    : 2021/12/29 17:49
# @author  : zza
# @Email   : 740713651@qq.com
# @File    : csv_model.py
from io import StringIO
from typing import Dict

import pandas
from pydantic import BaseModel


class CSVData(BaseModel):
    name: str = str()
    sep: str = ","
    data_types: Dict[str, str] = dict()
    file_buffer: str = ""

    def to_df(self):
        buffer = StringIO(self.file_buffer)
        buffer.seek(0)
        parse_dates = [k for k, v in self.data_types.items() if "<M8[ns]" == v]
        data_type = {}
        for k, v in self.data_types.items():
            if k in parse_dates:
                continue
            elif v.startswith("|"):
                data_type[k] = v[1:]
                continue
            else:
                data_type[k] = v
        new_df = pandas.read_csv(
            buffer,
            dtype=data_type,
            parse_dates=parse_dates,
            na_values="null",
            keep_default_na=False,
        )
        return new_df

    @classmethod
    def from_df(cls, df, name=""):
        buffer = StringIO()
        df.to_csv(buffer, index=False, na_rep="null")
        csv_data = cls(name=name)
        csv_data.data_types = {k: v.str for k, v in df.dtypes.items()}
        buffer.seek(0)
        csv_data.file_buffer = buffer.read()
        return csv_data
