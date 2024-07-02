#!/usr/bin/env python3
# Author: Ryan Boone
"""
Usage: scripts for running checksum (file transfer corruption) test
"""

import htcondor
import classad
import pathlib

def generate_submit_files(resources: dict):
    """
    Usage: creates submit files for the checksum job in Pool_Exerciser/submit_files/checksum_test/
    @param resources: dict whose keys are the GLIDEIN_ResourceName s to create submit files for
    """
    for resource in resources:
        with open(f"./submit_files/checksum_test/{resource}.sub", "w") as file:
            file.write("executable = ./executables/checksum_ex.py\n")
            file.write("arguments = torus.out0.07578.h5 torus.checksum\n")

            file.write("output = ./output_files/checksum_test/checksum.out\n")

            file.write("request_cpus = 1\n")
            file.write("request_memory = 1GB\n")
            file.write("request_disk = 5GB\n")

            file.write("should_transfer_files = yes\n")
            file.write("transfer_input_files = ./input_files/checksum_test/torus.out0.07578.h5, ./input_files/checksum_test/torus.checksum\n")

#           file.write("periodic_remove = JobStatus == 1 && CurrentTime-EnteredCurrentStatus > 60*5\n")
            file.write(f"Requirements = TARGET.GLIDEIN_ResourceName == \"{resource}\"\n")
            file.write("queue\n")

def run():
    """
    Usage: submits the test job to all sites specified by the submit files in
           Pool_Exerciser/submit_files/checksum_test/
    """
    schedd = htcondor.Schedd()
    submit_dir = pathlib.Path("./submit_files/checksum_test/")
    for file in submit_dir.iterdir():
        with open(file, "r") as submit_file:
            schedd.submit(htcondor.Submit(submit_file.read()))
