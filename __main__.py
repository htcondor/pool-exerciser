#!/usr/bin/env python3
# Author: Ryan Boone
"""
Usage: run the exerciser
"""

import htcondor
import classad

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "scripts/general"))
sys.path.append(os.path.join(os.path.dirname(__file__), "scripts/sleep_test"))

import query_collector
import sleep_scripts

#TODO: add cla options to choose test, for now just runs the sleep test
def main():
    resources = query_collector.get_resources()
    sleep_scripts.generate_submit_files(resources)
    sleep_scripts.run_as_individual_jobs(resources)

if __name__ == "__main__":
    sys.exit(main())

