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
import argparse


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


def run_exerciser(args: argparse.Namespace):
    """
    Usage: interprets cla and runs the exerciser based on the provided options
    @param args: program arguments as returned by parse_cla() in __main__
    """
    # -w option
    # changes location of working_dir, exiting if the dir dne
    if args.change_working_dir == None:
        working_dir = Path("working")
    else:
        working_dir = Path(args.change_working_dir)
        if not os.path.exists(working_dir):
            print("Error: Working dir must exist. Check arg val for -w and try again")
            print("Exiting...")
            sys.exit(1)

    # -t option
    # changes location of tests_dir, exiting if the dir dne
    if args.change_test_dir == None:
        tests_dir = Path("tests")
    else:
        tests_dir = Path(args.change_test_dir)
        if not os.path.exists(tests_dir):
            print("Error: Test dir must exist. Check arg val for -t and try again")
            print("Exiting...")
            sys.exit(1)

    # -s option
    # prints the list of currenlt available resources to the command line
    if args.snapshot:
        print("Here is a list of all currently available GLIDEIN_ResourceName s:")
        resources = get_resources()
        for resource in resources.keys():
            print(resource)
        print("End of resource list")

    # -p option
    # prints all the test names in tests_dir to the command line
    if args.print_tests:
        print("Here is a list of all tests in the test dir:")
        for test in tests_dir.iterdir():
            print(test.name)
        print("End of test list")

    # -f option
    # clears the working_dir
    if args.flush_all:
        print("Flushing entire working directory")
        for item in working_dir.iterdir():
            shutil.rmtree(item)

    # -d option
    # clears all timestamp_dirs in working_dir older than the date provided
    # will exit with an err if the date is not provided in the requested format
    if (not args.flush_by_date == None) and (not args.flush_all):
        print("Flushing by date")
        date = args.flush_by_date
        date_length = len(date)
        invalid_date = False
        try:
            if date_length == 4:
                format_date = datetime.strptime(date, "%Y")
            elif date_length == 7:
                format_date = datetime.strptime(date, "%Y-%m")
            elif date_length == 10:
                format_date = datetime.strptime(date, "%Y-%m-%d")
            elif date_length == 13:
                format_date = datetime.strptime(date, "%Y-%m-%d_%H")
            elif date_length == 16:
                format_date = datetime.strptime(date, "%Y-%m-%d_%H-%M")
            else:
                invalid_date = True
        except ValueError:
            invalid_date = True
        if invalid_date:
            print("Error: Invalid date str format. Check arg val for -d and try again")
            print("Exiting...")
            sys.exit(1)
        for subdir in working_dir.iterdir():
            subdir_date = datetime.strptime(subdir.name, "%Y-%m-%d_%H-%M")
            if subdir_date < format_date:
                shutil.rmtree(subdir)

    # -b option
    # controls whether the excersier runs. set to True by default
    if args.run:
        execute_tests(tests_dir, working_dir, args.tests)


def execute_tests(tests_dir: Path, working_dir: Path, test_list: list):
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

    for test in iter_tests(tests_dir, test_list):
        execute_dir, sub_file = create_test_execute_dir(timestamp_dir, test)

        root_dir = os.getcwd()
        schedd = htcondor2.Schedd()

        os.chdir(execute_dir)
        job = generate_sub_object(sub_file, test.name)
        item_data = [
            {"ResourceName": resource, "uniq_output_dir": f"results/{resource}"}
            for resource in resources.keys()
        ]

        job.issue_credentials()
        schedd.submit(job, itemdata=iter(item_data))
        os.chdir(root_dir)


def iter_tests(tests_dir: Path, test_list: list):
    """
    Usage: Iterate through the tests_dir and the test_list provided at the command line
    @param tests_dir: directory containing all available exerciser tests
    @param test_list: list provided as an arg at the command line. requested tests to run
    @return: generator of the tests that will be run by the exerciser
             only returns tests that appear in both tests_dir and test_list
             if test_list is empty, returns entire contents of tests_dir
    """
    if len(test_list) == 0:
        for test in tests_dir.iterdir():
            yield test
    else:
        for test in test_list:
            test_path = os.path.join(tests_dir, test)
            if os.path.exists(test_path):
                yield Path(test_path)
            else:
                print(f'Error: Invalid test "{test}", check arg val')
                print("Continuing with remaining tests...")


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
                    sub_file = Path(shutil.copy(item, execute_dir)).absolute()
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
                'Error: Test directory "{test_dir}" must contain only files, '
                + "directories and symlinks"
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
