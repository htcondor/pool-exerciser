#!/usr/bin/env python3
# Author: Ryan Boone
"""
Usage: create submit files for simple sleep test
Note: job will be evicted after 5 min in idle to test eviction ability
"""

import htcondor
import classad

def generate_submit_files(resources: dict):
    """
    Usage: creates submit files for the sleep job in Pool_Exerciser/submit_files/sleep_test
    @param resources: dict whose keys are all the unique GLIDEIN_ResourceName s currently
                      visible in the OSPool
    """
    for resource in resources:
        with open(f"./submit_files/sleep_test/{resource}.sub", "w") as file:
            file.write("executable = ./executables/sleep_test/sleep_ex.py\n")
            file.write("periodic_remove = JobStatus == 1 && CurrentTime-EnteredCurrentStatus > 60*5\n")
            file.write(f"Requirements = TARGET.GLIDEIN_ResourceName == \"{resource}\"\n")
            file.write("queue\n")

#TODO: remove param, use Path objects to get submit files
def run_as_individual_jobs(resources: dict):
    """
    Usage: runs the sleep job at all sites specified by the submit files seperately (not as dag)
    """
    schedd = htcondor.Schedd()
    for resource in resources:
        with open(f"./submit_files/sleep_test/{resource}.sub", "r") as submit_file:
            resource_submit = htcondor.Submit(submit_file.read())
            schedd.submit(resource_submit)

