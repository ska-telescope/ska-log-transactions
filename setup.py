#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools
from setuptools import setup

with open("README.md") as readme_file:
    readme = readme_file.read()

setup(
    name="ska_log_transactions",
    description="Square Kilometre Array transaction logging utility",
    long_description=readme + "\n\n",
    long_description_content_type='text/markdown',
    author="Anton Joubert",
    author_email="ajoubert+ska@ska.ac.za",
    url="https://gitlab.com/ska-telescope/ska-log-transactions",
    packages=setuptools.find_namespace_packages(where="src", include=["ska.*"]),
    package_dir={"": "src"},
    include_package_data=True,
    license="BSD license",
    zip_safe=False,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Astronomy",
    ],
    keywords="tango ska logging transactions",
    python_requires=">=3.5",
    test_suite="tests",
    install_requires=["katversion", "ska_logging >= 0.3.0", "ska-skuid"],
    use_katversion=True,
    tests_require=["tox"],
)
