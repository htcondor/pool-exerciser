#!/usr/bin/env python3
# Author: Ryan Boone
"""
Usage: functions used by exerciser operation
"""

import htcondor2
from pathlib import Path
import os
import sys
import shutil
from datetime import datetime


def get_resources() -> dict:
    """
    Usage: query the collector for a list of resources currently in the OSPool
    @return: dictionary whose keys are the names of all unique GLIDEIN_ResourceName s
             currently visible in the OSPool
    """
    collector = htcondor2.Collector("cm-1.ospool.osg-htc.org")
    resources = collector.query(
        ad_type=htcondor2.AdTypes.Startd,
        constraint="!isUndefined(GLIDEIN_ResourceName)",
        projection=["GLIDEIN_ResourceName"],
    )

    unique_resources = dict()

    for resource in resources:
        if resource["GLIDEIN_ResourceName"] in unique_resources:
            unique_resources[resource["GLIDEIN_ResourceName"]] += 1
        else:
            unique_resources[resource["GLIDEIN_ResourceName"]] = 1

    return unique_resources


def run_exerciser(tests_dir: Path, working_dir: Path, run=False):
    """
    Usage: calls necessary methods for setting up, running, and cleaning up exerciser
    @param tests_dir: directory containing all exerciser tests
    @param working_dir: directory for storing info on exerciser runs
    @param run: whether or not to create working file system and run tests
    """
    if run:
        execute_tests(tests_dir, working_dir)


def execute_tests(tests_dir: Path, working_dir: Path):
    """
    Usage: builds working file system and submits tests
    @param tests_dir: directory containing all exerciser tests
    @param working_dir: directory for storing info on exerciser runs
    """
    # create top level working dir for exerciser run
    curr_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
    timestamp_dir = os.path.join(working_dir, curr_time)
    if not os.path.exists(timestamp_dir):
        os.makedirs(timestamp_dir)

        # create text file with list of currently available ResourceNames
        with open(
            os.path.join(timestamp_dir, "resource_list.txt"), "w"
        ) as resource_list:
            resources = get_resources()
            for resource in resources.keys():
                resource_list.write(f"{resource}\n")
    else:
        # need to wait 1 min to allow for unique dir names
        print("Error: Please wait at least 1 minute between succesive runs")
        print("Exiting...")
        sys.exit(1)

    for test in tests_dir.iterdir():
        execute_dir, sub_file = create_test_execute_dir(timestamp_dir, test)

        root_dir = os.getcwd()
        schedd = htcondor2.Schedd()

        job = generate_sub_object(sub_file, test.name)
        item_data = [{"ResourceName": resource} for resource in resources.keys()]

        job.issue_credentials()
        os.chdir(execute_dir)
        schedd.submit(job, itemdata=iter(item_data))
        os.chdir(root_dir)


def create_test_execute_dir(timestamp_dir: Path, test_dir: Path) -> tuple:
    """
    Usage: prepares the execute dir by copying files from test_dir.
    @param timestamp_dir: parent of execute dir, which is the dst of file copy
    @param test_dir: src dir to copy from
    @return: tuple which stores the execute dir, and submit file for the test
    """
    execute_dir = os.path.join(timestamp_dir, test_dir.name)
    os.makedirs(execute_dir)

    sub_file_found = False

    for item in test_dir.iterdir():
        # copy files, watching for a single .sub file which is required
        if item.is_file():
            if item.name[-4:] == ".sub":
                if not sub_file_found:
                    sub_file = Path(shutil.copy(item, execute_dir))
                    sub_file_found = True
                else:
                    print(
                        f'Error: There can only be one .sub file in the test dir "{test_dir}"'
                    )
                    print("Exiting...")
                    sys.exit(1)
            else:
                shutil.copy(item, execute_dir)
        # copy an entire dir tree
        elif item.is_dir():
            shutil.copytree(item, os.path.join(execute_dir, item.name))
        # copy symlink
        elif item.is_symlink():
            shutil.copy(item, execute_dir)
        else:
            print(
                'Error: Test directory "{test_dir}" must contain only files, directories and symlinks'
            )
            print("Exiting...")
            sys.exit(1)

    if not sub_file_found:
        print(f'Error: There must be one .sub file in the test dir "{test_dir}"')
        print("Exiting...")
        exit(1)

    return (execute_dir, sub_file)


def generate_sub_object(sub_file: Path, test_name: str) -> htcondor2.Submit:
    """
    Usage: create an htcondor Submit object based on sub_file targetted to resource
    @param sub_file: general submit file to parse through to create Submit object
    @param test_name: name of the test as it appears in the Pool_Exerciser/tests/ dir
    """
    job = None
    with open(sub_file, "r") as f:
        job = htcondor2.Submit(f.read())
    if job is None:
        print(f"Error: Invalid submit file for test {test_name}")
        print("Exiting...")
        exit(1)

    # add requirement to land on target ResourceName
    req = job.get("Requirements")
    if req is None:
        job["Requirements"] = f'TARGET.GLIDEIN_ResourceName == "$(ResourceName)"'
    else:
        job["Requirements"] = (
            f'TARGET.GLIDEIN_ResourceName == "$(ResourceName)" && ' + req
        )

    # pool exerciser identifier attributes
    job["My.is_pool_exerciser"] = "true"
    job["My.pool_exerciser_test"] = test_name

    return job
