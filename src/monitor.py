#!/usr/bin/env python3
# Author: Ryan Boone
"""
Usage: run separately from exerciser to monitor the progress/outcomes of test runs
"""

from htcondor2 import JobEventLog
from htcondor2 import JobEventType
import sys
from pathlib import Path
import os
from datetime import datetime

def main():
    working_dir = Path("/home/rboone3/Pool_Exerciser/working")

    if not os.path.exists(working_dir):
        print("Error: Couldn't find working dir")
        sys.exit(1)

    if len(os.listdir(working_dir)) == 0:
        print("Error: Working directory is empty")
        sys.exit(1)

    target_dir = None
    for current_dir in working_dir.iterdir():
        if target_dir is None: target_dir = current_dir
        elif target_dir.name < current_dir.name: target_dir = current_dir
    
    status(target_dir)


def status(timestamp_dir: Path):
    """
    Usage: observe the shared log for an exerciser test run and print status information
    @param timestamp_dir: Path object to the root dir of an exerciser run
    """
    shared_log = os.path.join(timestamp_dir, "shared_exerciser.log")
    if not os.path.exists(shared_log):
        print(f"Error: Shared log does not exist for test run {timestamp_dir}")
        sys.exit(1)

    # print time info for exerciser run being analyzed, and the current time
    run_time = datetime.strptime(timestamp_dir.name, "%Y-%m-%d_%H-%M")
    curr_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Evaluating run from: {run_time}")
    print(f"Current time is: {curr_time}")
    
    # 2 dicts to store info on the status of the exerciser run
    # 1 for expected tests (appear in working dir)
    # 1 for unkown tests (don't appear in working dir, but do appear in shared log)
    # both are dicts of dicts. each subdict stores info for a single test
    # subdict fields are: submitted_resources, executed_resources,
    # succeeded_resources, failed_resources, aborted_resources
    expected_tests = {}
    unknown_tests = {}
    for item in timestamp_dir.iterdir():
        if (item.name != "resource_list.txt") and (item.name != "shared_exerciser.log"):
            test_dict = {
                "submitted_resources": [],
                "executed_resources": [],
                "succeeded_resources": [],
                "failed_resources": [],
                "aborted_resources": []
            }
            expected_tests[item.name] = test_dict

    # clusters dict to store mapping of event cluster to testname, "known" status, and list of
    # procs and their associated resources
    clusters = {}
    event_log = JobEventLog(shared_log)
    # loop through all events in shared event log, and filter for submit, execute, termination,
    # and abortion events
    for event in event_log.events(0):
        event_str = str(event)
        if event.type is JobEventType.SUBMIT:
            note_pos = event_str.rfind(":")
            if note_pos != -1:
                testname, resource = event_str[note_pos+1:-1].split(",")
                if testname in expected_tests.keys():
                    expected_tests[testname]["submitted_resources"].append(resource)
                    # add info to clusters to utilize for future execute, term, and abort events
                    if event.cluster not in clusters:
                        clusters[event.cluster] = {
                            "testname": testname,
                            "known": True,
                            "procs": {event.proc: resource}
                        }
                    else:
                        clusters[event.cluster]["procs"][event.proc] = resource
                else:
                    unknown_tests[testname]["submitted_resources"].append(resource)
                    if event.cluster not in clusters:
                        clusters[event.cluster] = {
                            "testname": testname,
                            "known": False,
                            "procs": {event.proc: resource}
                        }
                    else:
                        clusters[event.cluster]["procs"][event.proc] = resource
        elif event.type is JobEventType.EXECUTE:
            testname = clusters[event.cluster]["testname"]
            resource = clusters[event.cluster]["procs"][event.proc]
            known = clusters[event.cluster]["known"]
            
            if known:
                expected_tests[testname]["executed_resources"].append(resource)
            else:
                unknown_tests[testname]["executed_resources"].append(resource)
        elif event.type is JobEventType.JOB_TERMINATED:
            testname = clusters[event.cluster]["testname"]
            resource = clusters[event.cluster]["procs"][event.proc]
            known = clusters[event.cluster]["known"]

            if event_str.find("return value 0") != -1:
                if known:
                    expected_tests[testname]["succeeded_resources"].append(resource)
                else:
                    unknown_tests[testname]["succeeded_resources"].append(resource)
            else:
                if known:
                    expected_tests[testname]["failed_resources"].append(resource)
                else:
                    unknown_tests[testname]["failed_resources"].append(resource)
        elif event.type is JobEventType.JOB_ABORTED:
            testname = clusters[event.cluster]["testname"]
            resource = clusters[event.cluster]["procs"][event.proc]
            known = clusters[event.cluster]["known"]

            if known:
                expected_tests[testname]["aborted_resources"].append(resource)
            else:
                unknown_tests[testname]["aborted_resources"].append(resource)

    num_expected_tests = len(expected_tests)
    num_unknown_tests = len(unknown_tests)

    print(f"{num_expected_tests} expected tests run.")
    for test in expected_tests.keys():
        num_submitted_jobs = len(expected_tests[test]["submitted_resources"])
        num_executed_jobs = len(expected_tests[test]["executed_resources"])
        num_succeeded_jobs = len(expected_tests[test]["succeeded_resources"])
        num_failed_jobs = len(expected_tests[test]["failed_resources"])
        num_aborted_jobs = len(expected_tests[test]["aborted_resources"])

        print(f"For test {test}:")
        print(f"\t{num_submitted_jobs} resources submitted to")
        print(f"\t{num_executed_jobs} resources began execution")
        print(f"\t{num_succeeded_jobs} resources passed the test")
        print(f"\t{num_failed_jobs} resources failed the test. List of failed resources:")
        for resource in expected_tests[test]["failed_resources"]:
            print(f"\t\t{resource}")
        print(f"\t{num_aborted_jobs} resources aborted. List of aborted resources:")
        for resource in expected_tests[test]["aborted_resources"]:
            print(f"\t\t{resource}")

    print(f"{num_unknown_tests} unknown tests run.")
    for test in unknown_tests.keys():
        num_submitted_jobs = len(unknown_tests[test]["submitted_resources"])
        num_executed_jobs = len(unknown_tests[test]["executed_resources"])
        num_succeeded_jobs = len(unknown_tests[test]["succeeded_resources"])
        num_failed_jobs = len(unknown_tests[test]["failed_resources"])
        num_aborted_jobs = len(unknown_tests[test]["aborted_resources"])

        print(f"For test {test}:")
        print(f"\t{num_submitted_jobs} resources submitted to")
        print(f"\t{num_executed_jobs} resources began execution")
        print(f"\t{num_succeeded_jobs} resources passed the test")
        print(f"\t{num_failed_jobs} resources failed the test. List of failed resources:")
        for resource in unknown_tests[test]["failed_resources"]:
            print(f"\t\t{resource}")
        print(f"\t{num_aborted_jobs} resources aborted. List of aborted resources:")
        for resource in unknown_tests[test]["aborted_resources"]:
            print(f"\t\t{resource}")


if __name__ == "__main__":
    sys.exit(main())
