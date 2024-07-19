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

def make_working_subdirs(tests_dir: Path, working_dir: Path, curr_time: str):
    """
    Usage: create working subdirs in working_dir for each dir in tests_dir
    @param tests_dir: directory containing all exerciser tests
    @param working_dir: directory for storing info on exerciser runs
    @param curr_time: time in the format: %Y-%m-%d_%H:%M                
    """
    for test in tests_dir.iterdir():
        working_subdir_name = test.name + "_" + curr_time
        working_subdir = os.path.join(working_dir, working_subdir_name)

        if not os.path.exists(working_subdir):
            os.makedirs(working_subdir)
            copy_test_dir(test, working_subdir)
        else:
            # need to wait 1 min to allow for unique dir names
            print("Please wait at least 1 minute between succesive runs")
            sys.exit(0)

def copy_test_dir(test_dir: Path, working_subdir: Path):
    """
    Usage: copies the contents of test_dir into working_dir. preserves any
           subdir hierarchy
    @param test_dir: src dir to copy from
    @param working_subdir: dst dir to copy to
    """
    for item in test_dir.iterdir():
        if item.is_file():
            shutil.copy(item, working_subdir)
        elif item.is_dir():
            shutil.copytree(item, os.path.join(working_subdir, item.name))
        else:
            print("Test directory must only contain files and subdirectories")
            sys.exit(0)
