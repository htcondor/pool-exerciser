# How To Use Pool Exerciesr

## Running the Exerciser

The Pool Exerciser can be run with no options by navigating to the root directory **Pool_Exerciser** and running the command:

```
$ python __main__.py
```

This will create a timestamped execution directory in the **working** directory. It will then iterate
through the **tests** directory and copy the contents of them into the execution directory. Finally it
will submit all the tests in the execution directory to the OSPool. For more information about how
the Exerciser works, read Under_The_Hood.md

For more control over the Exerciser, there are a variety of command line options that can be
included.

## Command Line Options

- tests: positional argument. Takes a comma seperated list with the names of the tests you want
to run on the exerciser. If no tests are specified, the exerciser will execute all the tests in the
tests dir. Example:

```
$ python __main__.py checksum
# only the checksum test will be run
```

- --flush-all, -f: optional argument. Clears out all the previous executions subdirectories from
the working directory. If used with -w, it will clear out that working directory instead.

- --flush-by-date YYYY-MM-DD_hh-mm, -d YYYY-MM-DD_hh-mm: optional argument. Clears out execution
subdirectories from the working directory older than the date/time specified. You can use any level
of specificity from just YYYY to YYYY-MM-DD_hh-mm. Like -f, if used with -w, it will clear out that
working directory instead. Example:

```
$ python __main__.py -d 2024
# clears all exectution dirs older than 2024-01-01_00-00

$ python __main__.py -d 2024-07-31
# clears all execution dirs older than 2024-07-31_00-00

$ python __main__.py -d 2024-08-01_12-30
# clears all execution dirs older than 2024-08-01_12-30
```

- --print-tests, -p: optional argument. Prints out all the available tests from the test directory
and then exits without running the exerciser. If used with -t, it will print out the tests in that
test directory instead.

- --snapshot, -s: optional argument. Prints a list of all the resources currently in the OSPool and
then exits without running the exerciser.

- --working-dir dir_path, -w dir_path: optional argument. Specifies a diferent working directory
for the exerciser to execute in. Argument value should be a path string relative to the root 
Pool_Exerciser dir, or an abs path. Example:

```
$ python __main__.py -w ../../dir/subdir/new_working_dir
```

- --test-dir dir_path, -t dir_path: optional argument. Specifies a diferent test directory
for the exerciser to run tests from. It should contain tests formatted the same as the default tests
dir. Argument value should be a path string relative to the root Pool_Exerciser dir, or an abs path.
Example:

```
$ python __main__.py -t home/user/dir/subdir/new_tests_dir
```

- --block-run, -b: optional argument. Prevents the exerciser from executing.