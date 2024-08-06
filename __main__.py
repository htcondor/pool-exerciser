#!/usr/bin/env python3
# Author: Ryan Boone
"""
Usage: run the exerciser with a variety of options
"""

import argparse
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
        "tests",
        nargs="*",
        default=[],
        help="Comma separated list of specific tests to execute. "
        + "If not specified all available tests are executed.",
    )

    parser.add_argument(
        "-f",
        "--flush-all",
        action="store_true",
        dest="flush_all",
        help="Clears out all previous exerciser execution subdirectories "
        + "from the specified working directory.",
    )

    parser.add_argument(
        "-d",
        "--flush-by-date",
        metavar="YYYY-MM-DD_hh-mm",
        dest="flush_by_date",
        help=f"Removes all exerciser execution subdirectories in the specified "
        + "working directory older than the specified date/time. Note: "
        + "date/time can be any level of specificity from just YYYY to full "
        + "YYYY-MM-DD_hh-mm format.",
    )

    parser.add_argument(
        "-p",
        "--print-tests",
        action="store_true",
        dest="print_tests",
        help="prints the list of all available tests found in the specified test directory.",
    )

    parser.add_argument(
        "-s",
        "--snapshot",
        action="store_true",
        dest="snapshot",
        help="prints a list of all currently available resources in the pool.",
    )

    parser.add_argument(
        "-w",
        "--working-dir",
        metavar="directory_path",
        dest="working_dir",
        help="Specify a specific working directory for the exerciser to execute in.",
    )

    parser.add_argument(
        "-t",
        "--test-dir",
        metavar="directory_path",
        dest="test_dir",
        help="Specifies a directory containing available exerciser tests to execute.",
    )

    parser.add_argument(
        "-b",
        "--block-run",
        action="store_false",
        dest="run",
        help="Disables execution of tests.",
    )

    return parser.parse_args()


def process_cla(args: argparse.Namespace):
    """
    Usage: verification and processing of args returned by parse_cla()
    @param args: argparse.Namespace object returned by parse_cla()
    """
    if args.snapshot and args.print_tests:
        print("Error: Cannot select both --snapshot and --print-tests options at the same time")
        sys.exit(1)


def main():
    """
    Usage: run the thing
    """
    args = parse_cla()
    process_cla(args)
    general.run_exerciser(args)


if __name__ == "__main__":
    sys.exit(main())
