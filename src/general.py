#!/usr/bin/env python3
# Author: Ryan Boone
"""
Usage: scripts used by all or many tests
"""

import htcondor
import classad

def get_resources() -> dict:
    """
    Usage: query the collector for a list of resources currently in the OSPool
    @return: dictionary whose keys are the names of all unique GLIDEIN_ResourceName s
             currently visible in the OSPool
    """
    collector = htcondor.Collector()
    resources = collector.query(ad_type = htcondor.AdTypes.Startd,
                                constraint = "!isUndefined(GLIDEIN_ResourceName)",
                                projection = ["GLIDEIN_ResourceName"])

    unique_resources = dict()

    for resource in resources:
        if resource["GLIDEIN_ResourceName"] in unique_resources:
            unique_resources[resource["GLIDEIN_ResourceName"]] += 1
        else:
            unique_resources[resource["GLIDEIN_ResourceName"]] = 1

    return unique_resources
