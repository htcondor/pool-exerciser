# How To Add Tests To The Pool Exerciser

When building the Exerciser, care was taken to make the addition of new tests as simple as 
possible. If you have an HTCondor job, you can probably turn it into an Exerciser test! Jobs that
run on the Exerciser function just like normal HTCondor jobs, with a few small tweaks. To ensure
your test will work on the Exerciser, follow these practices:

- Move the folder containing all your test data into the tests dir. This should contain the HTCondor
submit file, any executable/s, and any other files necessary for proper test execution such as 
input files. Note that the name of this folder will be the name of the test known to the exerciser.
For example, inside the tests dir is the test "checksum" which contains all the data for that test.
The exerciser will refer to that test as "checksum" and all other tests the same way, so name this
folder what you want to name the test.

- Alternatively, you can specify a tests directory at runtime with the -t option. For more info on
this option, read How_To_Use_Exerciser. The tests inside this directory should follow the same
format as the default tests dir.

- Every test must have **EXACTLY ONE** HTCondor submit file, which is determined by the .sub file
extension. If your test contains no .sub file, or more than one, the exerciser will not attempt to
run it.

- There are a few special macros that you can use in your submit file. 

1. $(ResourceName) - This will be replaced with the target GLIDEIN_ResourceName for each job. This
may be of use to you, but is mostly used by the exerciser to target a specific resource.

2. $(uniq\_output\_dir) - This will create a results directory with subdirs for each Resource that
the test was submitted to. This is useful for organizing test output. For an example on how to use
this macro, you can inspect checksum.sub, which you can find in tests/checksum.
