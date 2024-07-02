#!/usr/bin/env python3
# Author: Ryan Boone
"""
Usage: run the exerciser with a variety of options
"""

import htcondor
import classad

import pathlib

import argparse

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "scripts"))

from scripts import general
from scripts import sleep_scripts
from scripts import checksum_scripts

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
    args = parse_cla()

    if args.flush_memory:
        submit_dir = pathlib.Path(f"./submit_files/{args.test_name}/")
        for file in submit_dir.iterdir():
            file.unlink()

    if args.query_collector:
        resources = general.get_resources()
        if (args.test_name == "sleep_test"):
            sleep_scripts.generate_submit_files(resources)
        if (args.test_name == "checksum_test"):
            checksum_scripts.generate_submit_files(resources)

    if args.run:
        if (args.test_name == "sleep_test"):
            sleep_scripts.run()
        if (args.test_name == "checksum_test"):
            checksum_scripts.run()

if __name__ == "__main__":
    sys.exit(main())

