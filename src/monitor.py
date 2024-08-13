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


#TODO: argparsing
# verbosity, working dir, test
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
        if target_dir is None:
            target_dir = current_dir
        elif target_dir.name < current_dir.name:
            target_dir = current_dir

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
    # 1 for expected tests (appears in working dir)
    # 1 for unkown tests (doesn't appear in working dir, but does appear in shared log)
    # both are dicts of dicts. each subdict stores info for a single test
    # subdict fields are: submitted_resources, executed_resources,
    # succeeded_resources, failed_resources, aborted_resources
    expected_tests = {}
    unknown_tests = {}
    for item in timestamp_dir.iterdir():
        # every dir represents a test
        if item.is_dir():
            test_dict = {
                "submitted_resources": [],
                "executed_resources": [],
                "succeeded_resources": [],
                "failed_resources": [],
                "aborted_resources": [],
            }
            expected_tests[item.name] = test_dict

    # clusters dict to store mapping of event cluster to test and associated procs
    clusters = {}
    event_log = JobEventLog(shared_log)
    # loop through all events in shared event log, and filter for submit, execute, termination,
    # and abortion events
    for event in event_log.events(0):
        # submit event: add test info to related dicts
        if event.type is JobEventType.SUBMIT:
            log_notes = event["LogNotes"]
            colon_pos = log_notes.find(":")
            if colon_pos != -1:
                testname, resource = log_notes[colon_pos + 1 :].split(",")
                if testname in expected_tests.keys():
                    expected_tests[testname]["submitted_resources"].append(resource)
                    # add info to clusters to utilize for future execute, term, and abort events
                    if event.cluster not in clusters:
                        clusters[event.cluster] = {
                            "testname": testname,
                            "known": True,
                            "procs": {event.proc: resource},
                        }
                    else:
                        clusters[event.cluster]["procs"][event.proc] = resource
                else:
                    unknown_tests[testname]["submitted_resources"].append(resource)
                    if event.cluster not in clusters:
                        clusters[event.cluster] = {
                            "testname": testname,
                            "known": False,
                            "procs": {event.proc: resource},
                        }
                    else:
                        clusters[event.cluster]["procs"][event.proc] = resource
            else:
                print("Error: Non-exerciser test found")
                sys.exit(1)
        # execute event: update executed_resources field in test subdict
        elif event.type is JobEventType.EXECUTE:
            testname = clusters[event.cluster]["testname"]
            resource = clusters[event.cluster]["procs"][event.proc]
            known = clusters[event.cluster]["known"]

            if known:
                expected_tests[testname]["executed_resources"].append(resource)
            else:
                unknown_tests[testname]["executed_resources"].append(resource)
        # termination event: determine test success or failure, then update related field
        elif event.type is JobEventType.JOB_TERMINATED:
            testname = clusters[event.cluster]["testname"]
            resource = clusters[event.cluster]["procs"][event.proc]
            known = clusters[event.cluster]["known"]

            if event["ReturnValue"] == 0:
                if known:
                    expected_tests[testname]["succeeded_resources"].append(resource)
                else:
                    unknown_tests[testname]["succeeded_resources"].append(resource)
            else:
                if known:
                    expected_tests[testname]["failed_resources"].append(resource)
                else:
                    unknown_tests[testname]["failed_resources"].append(resource)
        # abort event: update aborted_resources field in test subdict
        elif event.type is JobEventType.JOB_ABORTED:
            testname = clusters[event.cluster]["testname"]
            resource = clusters[event.cluster]["procs"][event.proc]
            known = clusters[event.cluster]["known"]

            if known:
                expected_tests[testname]["aborted_resources"].append(resource)
            else:
                unknown_tests[testname]["aborted_resources"].append(resource)
    print_status(expected_tests, unknown_tests, 0)


def print_status(expected_tests: dict, unknown_tests: dict, verbosity: int):
    """
    Usage: print the information gathered from the status method with a varying degree of verbosity
    @param expected_tests: dict of information on expected tests (appeared in working dir)
    @param unknown_tests: dict of info on unknown tests (appeared in shared log but not working dir)
    @param verbosity: int specifying level of verbosity with which to print status info
    """
    # print expected tests
    if len(expected_tests) > 0:
        print(f"{len(expected_tests)} expected tests run.")
        for test in expected_tests.keys():
            num_submitted_jobs = len(expected_tests[test]["submitted_resources"])
            num_executed_jobs = len(expected_tests[test]["executed_resources"])
            num_succeeded_jobs = len(expected_tests[test]["succeeded_resources"])
            num_failed_jobs = len(expected_tests[test]["failed_resources"])
            num_aborted_jobs = len(expected_tests[test]["aborted_resources"])

            if verbosity == 0:
                print(
                    f"{test} test: "
                    + f"{num_submitted_jobs} jobs submitted, "
                    + f"{num_succeeded_jobs} jobs passed, "
                    + f"{num_failed_jobs} jobs failed, "
                    + f"{num_aborted_jobs} system failures"
                )
            else:
                print(f"For test {test}:")
                print(f"\t{num_submitted_jobs} resources submitted to")
                print(f"\t{num_executed_jobs} resources began execution")
                print(f"\t{num_succeeded_jobs} resources passed the test")
                print(
                    f"\t{num_failed_jobs} resources failed the test. List of failed resources:"
                )
                for resource in expected_tests[test]["failed_resources"]:
                    print(f"\t\t{resource}")
                print(f"\t{num_aborted_jobs} resources aborted. List of aborted resources:")
                for resource in expected_tests[test]["aborted_resources"]:
                    print(f"\t\t{resource}")

    # print unknown tests
    if len(unknown_tests) > 0:
        print(f"{len(unknown_tests)} unknown tests run.")
        for test in unknown_tests.keys():
            num_submitted_jobs = len(unknown_tests[test]["submitted_resources"])
            num_executed_jobs = len(unknown_tests[test]["executed_resources"])
            num_succeeded_jobs = len(unknown_tests[test]["succeeded_resources"])
            num_failed_jobs = len(unknown_tests[test]["failed_resources"])
            num_aborted_jobs = len(unknown_tests[test]["aborted_resources"])

            if verbosity == 0:
                print(
                    f"{test} test: "
                    + f"{num_submitted_jobs} jobs submitted, "
                    + f"{num_succeeded_jobs} jobs passed, "
                    + f"{num_failed_jobs} jobs failed, "
                    + f"{num_aborted_jobs} system failures"
                )
            else:
                print(f"For test {test}:")
                print(f"\t{num_submitted_jobs} resources submitted to")
                print(f"\t{num_executed_jobs} resources began execution")
                print(f"\t{num_succeeded_jobs} resources passed the test")
                print(
                    f"\t{num_failed_jobs} resources failed the test. List of failed resources:"
                )
                for resource in unknown_tests[test]["failed_resources"]:
                    print(f"\t\t{resource}")
                print(f"\t{num_aborted_jobs} resources aborted. List of aborted resources:")
                for resource in unknown_tests[test]["aborted_resources"]:
                    print(f"\t\t{resource}")


if __name__ == "__main__":
    sys.exit(main())
