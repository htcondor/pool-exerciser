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

    parser.add_argument(
        "run-tests",
        nargs="*",
        default="all",
        help="specify the test/s to run in a space seperated list. if no tests "
        + "are listed, the exerciser will run all available tests.",
    )

    parser.add_argument(
        "-f",
        "--flush-all",
        action="store_true",
        help="deletes all subdirectories in /working",
    )

    # add ability to specify any amount of date string ex. 2024-04
    parser.add_argument(
        "-d",
        "--flush-by-date",
        metavar="YYYY-MM-DD_hh-mm",
        help=f"deletes all subdirectories in /working older than the arg value.\n"
        + "argument value must be given in YYYY-MM-DD_hh-mm format. "
        + "ex: 2024-07-31_15-57",
    )

    parser.add_argument(
        "-p",
        "--print-tests",
        action="store_true",
        help="print a list of all the available exerciser tests. "
        + "including this option prevents the exerciser from running",
    )

    parser.add_argument(
        "-s",
        "--snapshot",
        action="store_true",
        help="query the collector and print a list of currently available resources. "
        + "including this option prevents the exerciser from running",
    )

    parser.add_argument(
        "-w",
        "--change-working-directory",
        metavar="new_working_dir",
        help="changes the location of the root working dir to the specified dir for this run"
    )

    parser.add_argument(
        "-t",
        "--change-test-directory",
        metavar="new_test_dir",
        help="changes the location of the root test dir to the specified dir for this run",
    )

    return parser.parse_args()


def main():
    """
    Usage: run the thing
    """
    args = parse_cla()

    tests_dir = Path("tests")
    working_dir = Path("working")

    general.run_exerciser(tests_dir, working_dir, run=True)


if __name__ == "__main__":
    sys.exit(main())
