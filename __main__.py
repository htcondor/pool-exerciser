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
        "run_tests",
        nargs="*",
        default="all",
        help="specify the test/s to run in a space seperated list. if no tests "
        + "are listed, the exerciser will run all available tests.",
    )

    parser.add_argument(
        "-f",
        "--flush-all",
        action="store_true",
        help="deletes all subdirectories in the working dir. if this option is used with "
        + "-w, it will flush the contents of that dir rather than the default working dir.",
    )

    parser.add_argument(
        "-d",
        "--flush-by-date",
        metavar="YYYY-MM-DD_hh-mm",
        help=f"deletes all subdirectories in the working dir older than the arg value. "
        + "if this option is used with "
        + "-w, it will flush the contents of that dir rather than the default working dir. "
        + "argument value must include a year, but all other date specifications are optional. "
        + "if included, they must follow the YYYY-MM-DD_hh-mm format. for example, the following "
        + "are valid arg values (seperated by commas): 2024, 2024-07, 2024-07-30_02, "
        + "2024-07-31_14-53. but the following are invalid args: 202, 2024_14, 07-31, 2024-",
    )

    parser.add_argument(
        "-p",
        "--print-tests",
        action="store_true",
        help="print a list of all the available exerciser tests. if this option is used with "
        + "-t, it will print the contents of that dir rather than the default tests dir. ",
    )

    parser.add_argument(
        "-s",
        "--snapshot",
        action="store_true",
        help="query the collector and print a list of currently available resources. ",
    )

    parser.add_argument(
        "-w",
        "--change-working-dir",
        metavar="new_working_dir",
        help="changes the location of the working dir to the specified dir for this run. "
        + "the arg should be given as str representation of an absolute path to a dir, "
        + "or a relative path to the Pool_Exerciser root dir. "
        + "ex: -w ../../dir/subdir/new_working_dir",
    )

    parser.add_argument(
        "-t",
        "--change-test-dir",
        metavar="new_test_dir",
        help="changes the location of the test dir to the specified dir for this run. "
        + "the arg should be given as str representation of an absolute path to a dir, "
        + "or a relative path to the Pool_Exerciser root dir. "
        + "ex: -t ../../dir/subdir/new_test_dir"
    )

    parser.add_argument(
        "-b",
        "--block-run",
        action="store_true",
        help="selecting this option prevents the exerciser from running. all other options "
        + "will still be executed, so it can be useful if you wish to flush the working dir "
        + "without running a test, or use any other option"
    )

    return parser.parse_args()


def main():
    """
    Usage: run the thing
    """
    #args = parse_cla()
    #print(args)
    #exit(0)

    general.run_exerciser(parse_cla())


if __name__ == "__main__":
    sys.exit(main())
