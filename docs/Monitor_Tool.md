# Exerciser Monitor Tool

## Overview

The Pool Exerciser has a monitor tool that can be used to analyze Exerciser runs. You can run the
monitor by navigating to the **src** directory, and running the command:

```
$ python monitor.py
```

When run with no options, the monitor will analyze the most recent Exerciser run in the default
**working** directory. It iterates through an event log that is shared by all the tests that were
submitted in that particular run. It notes events such as job submissions, executions, terminations
via success or failure, and abortion due to periodic removal. It then prints a summary of all the
tests in that run.

## Command Line Options

There are a few options that can be selected to modify the monitors behavior.

- --verbosity, -v: optional argument. Increases the verbosity of the printed summary each time
this option is entered.

- --working-dir, -w: optional argument. Specifies a different working directory for the monitor to
search for executions in. Useful if you've used the -w option when running the Exerciser normally.

- --timestamp YYYY-MM-DD_hh-mm, -t YYYY-MM-DD_hh-mm: optional argument. Monitors a specific run
designated by the timestamp that it was submitted at. If this option is not included, the monitor
will check the status of the most recent run by default.
