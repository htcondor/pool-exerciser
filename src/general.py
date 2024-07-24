#!/usr/bin/env python3
# Author: Ryan Boone
"""
Usage: scripts used by all or many tests
"""

import htcondor2
from pathlib import Path
import os
import sys
import shutil

def get_resources() -> dict:
    """
    Usage: query the collector for a list of resources currently in the OSPool
    @return: dictionary whose keys are the names of all unique GLIDEIN_ResourceName s
             currently visible in the OSPool
    """
    collector = htcondor2.Collector("cm-1.ospool.osg-htc.org")
    resources = collector.query(ad_type = htcondor2.AdTypes.Startd,
                                constraint = "!isUndefined(GLIDEIN_ResourceName)",
                                projection = ["GLIDEIN_ResourceName"])

    unique_resources = dict()

    for resource in resources:
        if resource["GLIDEIN_ResourceName"] in unique_resources:
            unique_resources[resource["GLIDEIN_ResourceName"]] += 1
        else:
            unique_resources[resource["GLIDEIN_ResourceName"]] = 1

    return unique_resources

def make_working_subdirs(tests_dir: Path, working_dir: Path, curr_time: str, run=False):
    """
    Usage: create working subdirs in working_dir for each dir in tests_dir
    @param tests_dir: directory containing all exerciser tests
    @param working_dir: directory for storing info on exerciser runs
    @param curr_time: time in the format: %Y-%m-%d_%H:%M
    @param run: whether or not to submit the test jobs after creating working subdirs
    """

    # create top level working dir for exerciser run
    timestamp_subdir = os.path.join(working_dir, curr_time)
    if not os.path.exists(timestamp_subdir):
        os.makedirs(timestamp_subdir)
    else:
        # need to wait 1 min to allow for unique dir names
            print("Error: Please wait at least 1 minute between succesive runs")
            print("Exiting...")
            sys.exit(1)

    # create subdir for each test in tests_dir
    for test in tests_dir.iterdir():
        # make working subdir for test
        working_subdir = os.path.join(timestamp_subdir, test.name)
        os.makedirs(working_subdir)

        # copy contents of test dir into working subdir
        sub_file = copy_test_dir(test, working_subdir)

        # create text file with list of currently available ResourceNames
        with open(os.path.join(working_subdir, "resource_list.txt"), "w") as resource_list:
            resources = get_resources()
            for resource in resources:
                resource_list.write(f"{resource}\n")

        # create and submit jobs if run=True
        if run:
            root_dir = os.getcwd()
            schedd = htcondor2.Schedd()

            job = generate_sub_object(sub_file, resource, test.name)
            item_data = [{"ResourceName": resource} for resource in resources]

            job.issue_credentials()
            os.chdir(working_subdir)
            schedd.submit(job, itemdata = iter(item_data))
            os.chdir(root_dir)          

def copy_test_dir(test_dir: Path, working_subdir: Path) -> Path:
    """
    Usage: copies the contents of test_dir into working_dir. preserves any
           subdir hierarchy
    @param test_dir: src dir to copy from
    @param working_subdir: dst dir to copy to
    @return: path object to the submit file copy in the working subdir. error
             if there is not exactly one .sub file in the test dir
    """
    sub_file_found = False

    for item in test_dir.iterdir():
        # copy files, watching for a single .sub file which is required
        if item.is_file():
            if item.name[-4:] == ".sub":
                if not sub_file_found:
                    sub_file = Path(shutil.copy(item, working_subdir))
                    sub_file_found = True
                else:
                    print(f"Error: There can only be one .sub file in the test dir \"{test_dir}\"")
                    print("Exiting...")
                    sys.exit(1)
            else:
                shutil.copy(item, working_subdir)
        # copy an entire dir tree
        elif item.is_dir():
            shutil.copytree(item, os.path.join(working_subdir, item.name))
        # copy symlink
        elif item.is_symlink():
            shutil.copy(item, working_subdir)
        else:
            print("Error: Test directory \"{test_dir}\" must contain only files, directories and symlinks")
            print("Exiting...")
            sys.exit(1)
    
    if not sub_file_found:
        print(f"Error: There must be one .sub file in the test dir \"{test_dir}\"")
        print("Exiting...")
        exit(1)
    
    return sub_file

def run_exerciser(tests_dir: Path, working_dir: Path, curr_time: str, run=False):
    """
    Usage: calls necessary methods for setting up, running, and cleaning up exerciser
    @param tests_dir: directory containing all exerciser tests
    @param working_dir: directory for storing info on exerciser runs
    @param curr_time: time in the format: %Y-%m-%d_%H:%M
    @param run: whether or not to submit the test jobs after creating working subdirs
    """
    make_working_subdirs(tests_dir, working_dir, curr_time, run)

def generate_sub_object(sub_file: Path, resource: str, test_name: str) -> htcondor2.Submit:
    """
    Usage: create an htcondor Submit object based on sub_file targetted to resource
    @param sub_file: general submit file to parse through to create Submit object
    @param resource: target ResourceName as returned by the Collecter
    @param test_name: name of the test as it appears in the Pool_Exerciser/tests/ dir
    """
    job = None
    with open(sub_file, "r") as sub_file:
        job = htcondor2.Submit(sub_file.read())
    if job is None:
        print(f"Error: Invalid submit file for test {test_name}")
        print("Exiting...")
        exit(1)
    
    # add requirement to land on target ResourceName
    req = job.get("Requirements")
    if req is None:
        job["Requirements"] = f"TARGET.GLIDEIN_ResourceName == \"$(ResourceName)\""
    else:
        job["Requirements"] = f"TARGET.GLIDEIN_ResourceName == \"$(ResourceName)\" && " + req
    
    # pool exerciser identifier attributes
    job["My.is_pool_exerciser"] = "true"
    job["My.pool_exerciser_test"] = test_name

    return job
