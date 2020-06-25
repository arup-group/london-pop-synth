"""Packaging settings."""
import os

from setuptools import find_packages, setup

requirementPath="requirements.txt"
install_requires = []
if os.path.isfile(requirementPath):
    with open(requirementPath) as f:
        install_requires = f.read().splitlines()

setup(
    name="lps",
    version=0.0,
    description="A command line tool for synthesising populations.",
    packages=find_packages(exclude="tests*"),
    install_requires=install_requires,
    entry_points={"console_scripts": ["lps = lps.main:cli"]},
)
