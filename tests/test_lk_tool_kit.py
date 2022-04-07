#!/usr/bin/python3
# encoding: utf-8

"""
test_lk_tool_kit
----------------------------------

Tests for `lk_tool_kit` module.
"""
import pytest

import lk_tool_kit


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get("https://github.com/audreyr/cookiecutter-pypackage")


class TestLk_tool_kit:
    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    def setup_method(self):
        pass

    def teardown_method(self):
        pass

    def test_something(self, benchmark):
        assert lk_tool_kit.__version__
        from lk_tool_kit import __main__

        # assert cost time
        benchmark(__main__.version)
        assert benchmark.stats.stats.max < 0.01
