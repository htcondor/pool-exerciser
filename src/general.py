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
    # changes location of working_dir, creating the dir if needed
    if args.change_working_dir == None:
        working_dir = Path("working")
    else:
        working_dir = Path(args.change_working_dir)
        if not os.path.exists(working_dir):
            os.makedirs(working_dir)

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
        invalid_date = False
        try:
            if len(date) < 4:
                invalid_date = True
            if len(date) == 4:
                parsed_date = datetime.strptime(date, "%Y")
            if 4 < len(date) < 7:
                invalid_date = True
            if len(date) == 7:
                parsed_date = datetime.strptime(date, "%Y-%m")
            if 7 < len(date) < 10:
                invalid_date = True
            if len(date) == 10:
                parsed_date = datetime.strptime(date, "%Y-%m-%d")
            if 10 < len(date) < 13:
                invalid_date = True
            if len(date) == 13:
                parsed_date = datetime.strptime(date, "%Y-%m-%d_%H")
            if 13 < len(date) < 16:
                invalid_date = True
            if len(date) == 16:
                parsed_date = datetime.strptime(date, "%Y-%m-%d_%H-%M")
            if len(date) > 16:
                invalid_date = True
        except ValueError:
            invalid_date = True
        if invalid_date:
            print("Error: Invalid date str format. Check arg val for -d and try again")
            print("Exiting...")
            sys.exit(1)
        for subdir in working_dir.iterdir():
            subdir_date = datetime.strptime(subdir.name, "%Y-%m-%d_%H-%M")
            if subdir_date < parsed_date:
                shutil.rmtree(subdir)

    # -b option
    # prevents the exerciser from running
    if args.block_run:
        sys.exit(0)

    # run_tests postitional arg
    # if no arg/s are provided, runs every test in tests_dir
    # if arg/s are provided, only runs those tests
    # this is done by moving any unselected tests out of the tests_dir to a tmp_dir
    # then the exerciser is ran on the remaining tests in tests_dir
    # finally, all the tests in tmp_dir are moved back into tests_dir
    if args.run_tests == "all":
        execute_tests(tests_dir, working_dir)
    else:
        tmp_dir = Path("tmp")
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
            for test in tests_dir.iterdir():
                if test not in args.run_tests:
                    shutil.move(test, tmp_dir)
            execute_tests(tests_dir, working_dir)
            for test in tmp_dir.iterdir():
                shutil.move(test, tests_dir)
            shutil.rmtree(tmp_dir)
        else:
            print("Error: Cannot create dir named \"tmp\"")
            print("Exiting...")
            sys.exit(1)


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

        os.chdir(execute_dir)
        job = generate_sub_object(sub_file, test.name)
        item_data = [{"ResourceName": resource} for resource in resources.keys()]

        job.issue_credentials()
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
