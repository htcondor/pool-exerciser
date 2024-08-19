# Pool Exerciser

## Overview

The Pool Exerciser project was started as part of the 2024 Summer Fellowship Program at the 
Center for High Throughput Computing. It was developed by Fellow Ryan Boone and Mentors Cole Bollig 
and Rachel Lombardi. This project was based on the "IGWN Pool Exorciser" designed by James Clark.
His GitLab repository can be found here:
[IGWN Pool Exerciser](https://git.ligo.org/computing/distributed/igwn-pool-exorciser/-/blob/main/README.md?ref_type=heads)

## Background

The OSPool is a distributed collection of high throughput computing resources from institutions
around the world. This pool utilizes the HTCondor software suite to allow researchers to submit
their work to this system, which can drastically decrease the real-world time it takes for
their computations to complete. To learn more about the OSPool, you can visit their website here:
[OSPool](https://osg-htc.org/services/open_science_pool.html). To learn more about how this project 
uses the OSPool, you can read OSPool_Hierarchy.md, which you can find in the docs directory of this
repository.

## Goal

The aim of the project is to create an infrastructure to help analyze the state of the OSPool over 
time, by sending out tests to resources within the OSPool.

*Why analyze the OSPool?*

The OSPool is heterogeneous, because it is composed of computing resources from institutions with 
varying degrees of funding and staff support. It is also dynamic, because due to problems like
network outages, software updates, server issues, etc. resources may appear or dissapear from the
pool randomly, and without warning. Because of these factors, when problems occur in the OSPool they
are often difficult to locate. This was the inspiration for the Pool Exerciser project, which seeks 
to help find where these problems exist, so that solutions can be developed.

## Other Notes

This project was based on the "IGWN Pool Exorciser" designed by James Clark.
His GitLab repository can be found here:
[IGWN Pool Exerciser](https://git.ligo.org/computing/distributed/igwn-pool-exorciser/-/blob/main/README.md?ref_type=heads)