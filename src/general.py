#!/usr/bin/env python3
# Copyright 2024 HTCondor Team, Computer Sciences Department,
# University of Wisconsin-Madison, WI.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Usage: bulk of the code for exerciser execution
"""

__author__ = 'Ryan James Boone <rboone3@wisc.edu>'

import htcondor2
from pathlib import Path
import os
import sys
import shutil
from datetime import datetime
import argparse
from math import ceil

def get_resource_classad(cm: str = "cm-1.ospool.osg-htc.org") -> str:
    """
    Usage: determine the classad to query the central manager for the resource names
    @return: string of the classad of the desired resource name
    """
    if cm == "cm-1.ospool.osg-htc.org":
        resource_classad: str = "GLIDEIN_ResourceName"
    else:
        resource_classad = "Machine"
    
    return resource_classad


def get_resources(cm: str = "cm-1.ospool.osg-htc.org") -> dict:
    """
    Usage: query the collector for a list of resources currently in the OSPool
    @return: dictionary whose keys are the names of all unique ResourceName s
             currently visible in the HTCondor pool
    """
    collector = htcondor2.Collector(cm)

    resource_classad: str = get_resource_classad(cm)

    resources = collector.query(
        ad_type=htcondor2.AdTypes.StartDaemon,
        constraint=f"!isUndefined({resource_classad})",
        projection=[resource_classad],
    )

    unique_resources = dict()

    # eliminate repeat resources to produce a unique list
    # using a dictionary to count number of occurrences, but this count is unused at the moment
    for resource in resources:
        if resource[resource_classad] in unique_resources:
            unique_resources[resource[resource_classad]] += 1
        else:
            unique_resources[resource[resource_classad]] = 1

    return unique_resources


def run_exerciser(args: argparse.Namespace):
    """
    Usage: interprets cla and runs the exerciser based on the provided options
    @param args: program arguments as returned by parse_cla() in __main__
    """
    # -w option
    # changes location of working_dir, exiting if the dir dne
    if args.working_dir is None:
        working_dir = Path("working")
    else:
        working_dir = Path(args.working_dir)
        if not os.path.exists(working_dir):
            print(f"Error: Specified working directory {working_dir} does not exist")
            sys.exit(1)

    # -t option
    # changes location of tests_dir, exiting if the dir dne
    if args.test_dir is None:
        tests_dir = Path("tests")
    else:
        tests_dir = Path(args.test_dir)
        if not os.path.exists(tests_dir):
            print(f"Error: Specified test directory {tests_dir} does not exist")
            sys.exit(1)

    # -s option
    # prints the list of currenlt available resources to the command line
    if args.snapshot:
        print("Here is a list of all currently available resources:")
        resources = get_resources(args.central_manager)
        for resource in resources.keys():
            print(f'  {resource}')
        print("End of resource list")
        sys.exit(0)

    # -p option
    # prints all the test names in tests_dir to the command line
    if args.print_tests:
        print("Here is a list of all tests in the test dir:")
        for test in tests_dir.iterdir():
            print(f'  {test.name}')
        print("End of test list")
        sys.exit(0)

    # -f option
    # clears the working_dir
    if args.flush_all:
        print("Flushing entire working directory")
        for item in working_dir.iterdir():
            shutil.rmtree(item)
    # -d option
    # clears the working_dir by the provided date
    elif args.flush_by_date is not None:
        print("Flushing working directory by date")
        format_date = parse_date(args.flush_by_date)
        for subdir in working_dir.iterdir():
            subdir_date = datetime.strptime(subdir.name, "%Y-%m-%d_%H-%M")
            if subdir_date < format_date:
                shutil.rmtree(subdir)

    # -b option
    # controls whether the excersier runs. set to True by default
    if args.run:
        execute_tests(tests_dir, working_dir, args.tests, args.resource_sample_size, args.central_manager)


def parse_date(date_from_cla: str) -> str:
    """
    Usage: parse through date_time argument from the command line (option -d)
    @param date_from_cla: date string as entered at the command line
    @return: datetime formatted str representation of the date_from_cla
    """
    DATETIME_FORMAT_OPTS = {"date": ["%Y", "%m", "%d"], "time": ["%H", "%M"]}

    # YYYY-MM-DD_HH-MM
    num_hyphens = date_from_cla.count("-")
    if num_hyphens > 3 or (num_hyphens == 3 and "_" not in date_from_cla):
        print(
            f"Error: Invalid date time '{date_from_cla}' provided from --flush-by-date"
        )
        sys.exit(1)

    date_fmt = "-".join(DATETIME_FORMAT_OPTS["date"][: min(num_hyphens + 1, 3)])
    date_fmt += (
        "_" + "-".join(DATETIME_FORMAT_OPTS["time"][: num_hyphens - 1])
        if "_" in date_from_cla
        else ""
    )

    try:
        format_date = datetime.strptime(date_from_cla, date_fmt)
    except ValueError:
        print(
            f"Error: Invalid date time '{date_from_cla}' provided from --flush-by-date"
        )
        sys.exit(1)

    return format_date


def execute_tests(tests_dir: Path, working_dir: Path, test_list: list, sample_percent: float,
                  cm: str):
    """
    Usage: builds working file system and submits tests
    @param tests_dir: directory containing all exerciser tests
    @param working_dir: directory for storing info on exerciser runs
    @param test_list: list parsed from args of all the tests to run
    @param sample_percent: percent of machines to send tests to in each resource
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
            resources = get_resources(cm)
            for resource in resources.keys():
                resource_list.write(f"{resource}\n")
    else:
        # need to wait 1 min to allow for unique dir names
        print("Error: Please wait at least 1 minute between succesive runs")
        sys.exit(1)

    resource_classad: str = get_resource_classad(cm)

    # where the magic happens!
    # loop through every test returned by iter_tests, create execution dirs for them using
    # create_test_execute_dir, prepare them with generate_sub_object, and then submit them to the
    # OSPool!
    # i.e. verify that the requested tests exist, make spaces for them to run, modify them into
    # exerciser jobs, and send them to the pool
    for test in iter_tests(tests_dir, test_list):
        execute_dir, sub_file = create_test_execute_dir(timestamp_dir, test)
        abs_timestamp_dir = os.path.abspath(timestamp_dir)

        root_dir = os.getcwd()
        schedd = htcondor2.Schedd()

        os.chdir(execute_dir)
        job = generate_sub_object(sub_file, test.name, abs_timestamp_dir, resource_classad)

        item_data = []
        for resource in resources.keys():
            resource_size = resources[resource]
            sample_size = ceil(resource_size * sample_percent)
            for i in range(sample_size):
                item = {
                    "ResourceName": resource,
                    "resource_dir": f"results/{resource}",
                    "sample_dir": f"results/{resource}/sample_{i:03}",
                    "SampleNumber": str(i)
                }
                item_data.append(item)

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
                print(
                    f'Warning: Specified test "{test}" not found. Continuing with other tests'
                )


def create_test_execute_dir(timestamp_dir: Path, test_dir: Path) -> tuple:
    """
    Usage: prepares the execute dir by copying files from test_dir.
    @param timestamp_dir: parent of execute dir, which is the dst of file copy
    @param test_dir: src dir to copy from
    @return: tuple which stores the execute dir, and submit file for the test
    """
    # create execution dir for specified test
    execute_dir = os.path.join(timestamp_dir, test_dir.name)
    os.makedirs(execute_dir)

    # look for the submit file in the test dir. each test must contain exactly 1
    sub_file_found = False

    # copy files from test dir into execution dir. watch for .sub file
    for item in test_dir.iterdir():
        if item.is_file():
            # .sub file found
            if item.name[-4:] == ".sub":
                # first occurrence (good)
                if not sub_file_found:
                    sub_file = Path(shutil.copy(item, execute_dir)).absolute()
                    sub_file_found = True
                # second occurrence (bad)
                else:
                    print(
                        f'Error: There can only be one .sub file in the test dir "{test_dir}"'
                    )
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
            sys.exit(1)

    if not sub_file_found:
        print(f'Error: There must be one .sub file in the test dir "{test_dir}"')
        sys.exit(1)

    return (execute_dir, sub_file)


def generate_sub_object(
        sub_file: Path, test_name: str, timestamp_dir: str, 
        resource_classad: str = "GLIDEIN_ResourceName"
        ) -> htcondor2.Submit:
    """
    Usage: create an htcondor Submit object based on sub_file targetted to resource
    @param sub_file: general submit file to parse through to create Submit object
    @param test_name: name of the test as it appears in the tests dir
    @param timestamp_dir: str rep of absolute path to top level dir of each exerciser execution
    """
    # create submit object
    job = None
    with open(sub_file, "r") as f:
        job = htcondor2.Submit(f.read())
    if job is None:
        print(f"Error: Invalid submit file for test {test_name}")
        sys.exit(1)

    job.setSubmitMethod(99, True)

    # add requirement to land on target ResourceName
    req_expr = f'TARGET.{resource_classad} == "$(ResourceName)"'
    req = job.get("Requirements")
    job["Requirements"] = req_expr if req is None else req_expr + f" && ({req})"

    # add periodic removal statement
    # job should be removed if it is in idle or running for more than 4 hours, if it ever
    # goes on hold, or if it restarts more than 10 times
    sec_in_4hr = 60 * 60 * 4
    prdc_rm_expr = (
        f"(JobStatus == 1 && CurrentTime-EnteredCurrentStatus > {sec_in_4hr}) || "
        + f"(JobStatus == 2 && CurrentTime-EnteredCurrentStatus > {sec_in_4hr}) || "
        + "(JobStatus == 5) || "
        + "(NumShadowStarts > 10)"
    )
    prdc_rm = job.get("periodic_remove")
    job["periodic_remove"] = prdc_rm_expr if prdc_rm is None else prdc_rm_expr + f" || ({prdc_rm})"   

    # create shared log for each exerciser run to be used by monitor prog
    job["dagman_log"] = os.path.join(timestamp_dir, "shared_exerciser.log")

    # create submit notes to identify job by the testname and expected resource
    job["submit_event_notes"] = f"exerciser_info:{test_name},$(ResourceName),$(SampleNumber)"

    # add execute attributes
    job["ulog_execute_attrs"] = resource_classad

    # add pool exerciser identifier attributes
    job["My.EXERCISER_Job"] = "true"
    job["My.EXERCISER_TestName"] = test_name
    job["My.EXERCISER_SampleNum"] = "$(SampleNumber)"

    return job
