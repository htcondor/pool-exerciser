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
import argparse


def parse_cla() -> argparse.Namespace:
    """
    Usage: command line argument parser
    @return: parsed arguments in argparse.Namespace object
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-v",
        "--verbosity",
        action="count",
        dest="verbosity",
        default=0,
        help="Increases the verbosity of print stmts with each included -v"
    )

    parser.add_argument(
        "-w",
        "--working-dir",
        metavar="directory_path",
        dest="working_dir",
        help="Specify a specific working directory for the monitor to examine.",
    )

    parser.add_argument(
        "-t",
        "--timestamp",
        metavar="YYYY-MM-DD_hh-mm",
        dest="timestamp",
        help="Specify the timestamp of an exerciser run to target with the monitor. Must include "
        + "entire YYYY-MM-DD_hh-mm string."
    )

    return parser.parse_args()


def main():
    """
    Usage: monitor the status of a specified exerciser run
    """
    args = parse_cla()

    # -w option
    # changes location of working_dir, exiting if the dir dne
    if args.working_dir is None:
        working_dir = Path("../working")
    else:
        working_dir = Path(args.working_dir)
        if not os.path.exists(working_dir):
            print(f"Error: Specified working directory {working_dir} does not exist")
            sys.exit(1)

    if not os.path.exists(working_dir):
        print("Error: Couldn't find working dir. Ensure you are in source directory")
        sys.exit(1)

    if len(os.listdir(working_dir)) == 0:
        print("Working directory is empty, nothing to monitor")
        sys.exit(0)

    # -t option
    # specifies exerciser run to analyze. if no timestamp is provided, analyzes most recent run
    if args.timestamp is None:
        target_dir = None
        for current_dir in working_dir.iterdir():
            if target_dir is None:
                target_dir = current_dir
            elif target_dir.name < current_dir.name:
                target_dir = current_dir
    else:
        target_dir = os.path.join(working_dir, args.timestamp)
        if not os.path.exists(target_dir):
            print(f"Error: Specified exerciser execution directory {args.timestamp} does not exist")
            sys.exit(1)
        target_dir = Path(target_dir)

    status(target_dir, args.verbosity)


def status(timestamp_dir: Path, verbosity: int):
    """
    Usage: observe the shared log for an exerciser test run and print status information
    @param timestamp_dir: Path object to the root dir of an exerciser run
    @param verbosity: int specifying how verbose the print stmts should be
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
            if ":" in log_notes:
                testname, resource = log_notes.split(":")[1].split(",")

                # add info to clusters to utilize for future execute, term, and abort events
                if event.cluster not in clusters:
                    clusters[event.cluster] = {
                        "testname": testname,
                        "known": True,
                        "procs": {event.proc: resource},
                    }
                else:
                    clusters[event.cluster]["procs"][event.proc] = resource

                if testname in expected_tests.keys():
                    expected_tests[testname]["submitted_resources"].append(resource)
                else:
                    unknown_tests[testname]["submitted_resources"].append(resource)
                    clusters[event.cluster]["known"] = False
            else:
                print("Error: Non-exerciser test found in shared log")
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

    print_status(expected_tests, unknown_tests, verbosity)


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

            print(
                f"{test} test: "
                + f"{num_submitted_jobs} jobs submitted, "
                + f"{num_succeeded_jobs} jobs passed, "
                + f"{num_failed_jobs} jobs failed, "
                + f"{num_aborted_jobs} system failures"
            )
            if verbosity > 0:
                print(
                    f"\t{num_failed_jobs} jobs failed the test. List of failed job resources:"
                )
                for resource in expected_tests[test]["failed_resources"]:
                    print(f"\t\t{resource}")
                print(f"\t{num_aborted_jobs} system failures. List of sys fail resources:")
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
            
            print(
                f"{test} test: "
                + f"{num_submitted_jobs} jobs submitted, "
                + f"{num_succeeded_jobs} jobs passed, "
                + f"{num_failed_jobs} jobs failed, "
                + f"{num_aborted_jobs} system failures"
            )
            if verbosity > 0:
                print(
                    f"\t{num_failed_jobs} jobs failed the test. List of failed job resources:"
                )
                for resource in unknown_tests[test]["failed_resources"]:
                    print(f"\t\t{resource}")
                print(f"\t{num_aborted_jobs} system failures. List of sys fail resources:")
                for resource in unknown_tests[test]["aborted_resources"]:
                    print(f"\t\t{resource}")


if __name__ == "__main__":
    sys.exit(main())
