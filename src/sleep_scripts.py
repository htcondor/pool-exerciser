#!/usr/bin/env python3
# Author: Ryan Boone
"""
Usage: scripts for running simple sleep test
Note: job will be evicted after 5 min in idle to test eviction ability
"""

import htcondor
import classad
import pathlib

def generate_submit_files(resources: dict):
    """
    Usage: creates submit files for the sleep job in Pool_Exerciser/submit_files/sleep_test/
    @param resources: dict whose keys are the GLIDEIN_ResourceName s to create submit files for
    """
    for resource in resources:
        with open(f"./submit_files/sleep_test/{resource}.sub", "w") as file:
            file.write("executable = ./tests/sleep_ex.py\n")
            file.write("periodic_remove = JobStatus == 1 && CurrentTime-EnteredCurrentStatus > 60*5\n")
            file.write(f"Requirements = TARGET.GLIDEIN_ResourceName == \"{resource}\"\n")
            file.write("queue\n")

def run():
    """
    Usage: submits the sleep test job at all sites specified by the submit files in
           Pool_Exerciser/submit_files/sleep_test/
    """
    schedd = htcondor.Schedd()
    submit_dir = pathlib.Path("./submit_files/sleep_test/")
    for file in submit_dir.iterdir():
        with open(file, "r") as submit_file:
            schedd.submit(htcondor.Submit(submit_file.read()))
