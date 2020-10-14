#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

requirements = ["pymodbus==2.4.0"]

test_requirements = [
    "pytest>=3",
]

setup(
    author="Fabian Göttel",
    author_email="fabian.goettel@gmail.com",
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        'Programming Language :: Python :: 3.9"',
    ],
    description="Connect a Schwörer WGT to your home",
    install_requires=requirements,
    long_description=readme,
    include_package_data=True,
    keywords="wgt",
    name="wgt",
    packages=find_packages(include=["wgt", "wgt.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/fgoettel/wgt",
    version="0.3.2",
    zip_safe=False,
)
