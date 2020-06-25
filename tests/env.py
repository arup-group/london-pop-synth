"""
Test environment setup.
"""

import sys
import os
from pathlib import Path


def this_dir():
    return Path(os.path.abspath(__file__)).parent


def root():
    return this_dir().parent


def set_module():
    sys.path.append(os.path.abspath('../lps'))


test_in_path = '<REMOVED>'
test_out_path = this_dir() / 'test_out'
test_config = this_dir() / 'test_synth.toml'
