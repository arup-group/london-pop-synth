"""Packaging settings."""

from setuptools import find_packages, setup

setup(
    name="lps",
    version=0.0,
    description="A command line tool for synthesising populations.",
    packages=find_packages(exclude="tests*"),
    entry_points={"console_scripts": ["lps = lps.main:cli"]},
)
