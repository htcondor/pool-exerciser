#!/usr/bin/env python3
# Author: Ryan Boone
"""
Usage: use sha256sum to test for file transfer corruption
"""

import hashlib
import sys

with open(sys.argv[1], "rb") as file:
    file_data = file.read()
    file_hash = hashlib.sha256(file_data).hexdigest()

with open(sys.argv[2], "r") as checksum_file:
    checksum_data = checksum_file.readline()[0:-1]

if file_hash == checksum_data:
    print("file transferred successfully")
else:
    print("file transfer error")
