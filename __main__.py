#!/usr/bin/env python3
# Author: Ryan Boone
"""
Usage: run the exerciser with a variety of options
"""

from pathlib import Path
import argparse
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from src import general

def parse_cla() -> argparse.Namespace:
    """
    Usage: command line argument parser
    @return: parsed arguments in argparse.Namespace object
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("test_name",
                        type=str,
                        metavar="test_name",
                        choices=["sleep_test", "checksum_test"],
                        help="name of test to be run by exerciser")

    parser.add_argument("-f",
                        "--flush-memory",
                        action="store_true",
                        help="clears all .sub files for {test_name}")

    parser.add_argument("-q",
                        "--query-collector",
                        action="store_true",
                        help="queries collector for a list of current ResourceName s in the OSPool. " +
                             "overwrites any existing .sub files which match the current list, and ignores any which do not")

    parser.add_argument("-r",
                        "--run",
                        action="store_true",
                        help="runs the exerciser on {test_name} for any existing submit files. if no submit files exist, does nothing")

    return parser.parse_args()

def main():
    """
    Usage: run the thing
    """
    curr_time = datetime.now().strftime("%Y-%m-%d_%H:%M")
    tests_dir = Path("tests")
    working_dir = Path("working")

    general.run_exerciser(tests_dir, working_dir, curr_time, run=True)

if __name__ == "__main__":
    sys.exit(main())
