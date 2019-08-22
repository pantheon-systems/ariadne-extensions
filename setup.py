#!/usr/bin/env python

from os import path

from setuptools import setup

with open(path.join(path.abspath(path.dirname(__file__)), "README.md"), encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()


TEST_DEPENDECIES = ["pytest-cov", "pytest", "pylint", "pytest-runner", "black", "coveralls"]

INSTALL_DEPENDECIES = ["ariadne"]

setup(
    name="ariadne-extensions",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    version="0.1.3",
    url="https://github.com/aleszoulek/ariadne-extensions",
    author="Ales Zoulek",
    author_email="ales.zoulek@gmail.com",
    packages=["ariadne_extensions"],
    setup_requires=[],
    install_requires=INSTALL_DEPENDECIES,
    tests_require=TEST_DEPENDECIES,
    extras_require={"test": TEST_DEPENDECIES},
)
