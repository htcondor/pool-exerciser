#!/usr/bin/env python3
# Author: Ryan Boone
"""
Usage: use sha256sum to test for file transfer corruption
"""

import hashlib
import sys

with open(sys.argv[1], "rb") as output_file:
    file_data = output_file.read()
    file_hash = hashlib.sha256(file_data).hexdigest()

with open(sys.argv[2], "r") as sha_file:
    sha_file_data = sha_file.readline()[0:-1]

if file_hash == sha_file_data:
    print("file transferred successfully")
else:
    print("file transfer error")
