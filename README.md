# Pool Exerciser

The goal of the Pool Exerciser is to provide an infrastructure that collects
accurate, reliable data about the current state of the OSPool. It then uses
that information to send out samples of test jobs to specific locations in
the OSPool. 

Tests can be added by writing an HTCondor submit file and an executable,
 and can then be run on the existing Pool Exerciser infrastructure.

This project was based on the "IGWN Pool Exorciser" designed by James Clark.
His GitLab repository can be found here:
[IGWN Pool Exerciser](https://git.ligo.org/computing/distributed/igwn-pool-exorciser/-/blob/main/README.md?ref_type=heads)

## Functionality

The exerciser works by querying the central manager's collector to obtain
a list of all the resources currently available in the OSPool. It then
creates working directories for each selected test. 

## Usage

The Exerciser can be run with a variety of options. Be sure to run all commands
from the parent directory: /Pool_Exerciser

To display all available options, run the command:

```
$ python __main__.py --help
```

Some helpful options to remember:

```
$ python __main__.py test_name --flush-memory
# clears all submit files from the directory: /Pool_Exerciser/submit_files/test_name

$ python __main__.py test_name --query-collector
# queries the collector for a list of current ResourceNames in the OSPool, and
# generates sbumit files for every ResourceName in /Pool_Exerciser/submit_files/test_name

$ python __main__.py test_name --run
# submits all jobs for the test "test_name"
# i.e. runs condor_submit on all .sub files in /Pool_Exerciser/submit_files/test_name
```
