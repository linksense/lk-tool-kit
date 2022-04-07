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
    """csv 转 pydantic Model 工具

    >>> import numpy
    >>> df = pandas.DataFrame(numpy.random.randint(0, 100, size=(100, 2)), columns=['a', 'b'])
    >>> df['c'] = pandas.date_range(start='20220106',periods=100)
    >>> df['d'] = df['c'].apply(str)
    >>> csv_data = CSVData.from_df(df)
    >>> df_data = csv_data.to_df()
    >>> assert df.equals(df_data)
    """

    name: str = str()
    sep: str = ","
    data_types: Dict[str, str] = dict()
    file_buffer: str = ""

    def to_df(self) -> pandas.DataFrame:
        buffer = StringIO(self.file_buffer)
        buffer.seek(0)
        parse_dates = [k for k, v in self.data_types.items() if "<M8[ns]" == v]
        data_type = {}
        for _key, _value in self.data_types.items():
            if _key in parse_dates:  # datetime
                continue
            elif _value.startswith("|"):
                data_type[_key] = _value[1:]
                continue
            else:
                data_type[_key] = _value
        new_df = pandas.read_csv(
            buffer,
            dtype=data_type,
            parse_dates=parse_dates,
            na_values="null",
            keep_default_na=False,
        )
        return new_df

    @classmethod
    def from_df(cls, df: pandas.DataFrame, name: str = "") -> "CSVData":
        buffer = StringIO()
        df.to_csv(buffer, index=False, na_rep="null")
        csv_data = cls(name=name)
        csv_data.data_types = {k: v.str for k, v in df.dtypes.items()}
        buffer.seek(0)
        csv_data.file_buffer = buffer.read()
        return csv_data
