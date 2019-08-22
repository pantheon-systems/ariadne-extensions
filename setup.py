#!/usr/bin/env python

from os import path

from setuptools import setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


TEST_DEPENDECIES = ["pytest-cov", "pytest", "pylint", "pytest-runner"]

INSTALL_DEPENDECIES = ["ariadne"]

setup(
    name="ariadne-extensions",
    long_description=long_description,
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
