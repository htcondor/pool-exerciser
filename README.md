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
uses the OSPool, you can read OSPool_Hierarchy, which you can find in the docs directory of this
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

## Usage

The Exerciser can be run in its most basic form by navigating to the root directory
**Pool_Exerciser** and running the command:

```
$ python __main__.py
```

For more information on command line options, you can add -h to the command:

```
$ python __main__.py -h
```

For in depth information on running the Exerciser, read How_To_Use_Exerciser in the **docs**
directory of this repository.

At the moment, the only test existing in the Exerciser is the checksum test. This test uses a large
input file which is too gib to store on GitHub. If you wish to run this test, run the following
commands from the root directory **Pool_Exerciser**. This will copy the file into the proper test
directory.

```
$ cd tests/checksum
$ stashcp osdf:///ospool/uc-shared/public/OSG-Staff/pool-exerciser/input.h5 .
```

## Other Notes

This project was inspired by the "IGWN Pool Exorciser" designed by James Clark.
His GitLab repository can be found here:
[IGWN Pool Exerciser](https://git.ligo.org/computing/distributed/igwn-pool-exorciser/-/blob/main/README.md?ref_type=heads)