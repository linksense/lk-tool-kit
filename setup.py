#!/usr/bin/python3
# encoding: utf-8
"""A setuptools based setup module for lk_tool_kit"""

from codecs import open
from os import path
from setuptools import setup, find_packages

import versioneer

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as readme_file:
    readme = readme_file.read()

with open(path.join(here, "HISTORY.md"), encoding="utf-8") as history_file:
    history = history_file.read()

with open(path.join(here, "requirements.txt"), encoding="utf-8") as requirements_file:
    requirements = requirements_file.read()

requirements_dev = """
pytest
coverage
mock
pytest-timeout
pytest-benchmark
isort
typing_extensions

# Linting
flake8
flake8-black
flake8-import-order
flake8-bandit
flake8-annotations
flake8-builtins
flake8-variables-names
flake8-functions ; python_version > '3.6'
flake8-expression-complexity
"""
ext_modules = []
setup(
    name="lk_tool_kit",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="lk tool kit package",
    long_description=readme + "\n\n" + history,
    author="zza",
    author_email="740713651@qq.com",
    url="https://github.com/zza/lk-tool-kit",
    packages=find_packages(include=["lk_tool_kit", "lk_tool_kit.*"]),
    entry_points={
        "console_scripts": [
            # "lk_tool_kit=lk_tool_kit.__main__:entry_point",
        ],
    },
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    extras_require={"dev_require": requirements + "\n" + requirements_dev},
    ext_modules=ext_modules,
    keywords="lk_tool_kit",
)
