#! /usr/bin/python
# tests/list-instances.py (Python script) -- tests boto_helper.Credentials using EC2

from __future__ import print_function

import boto.ec2

import boto_helper

c = boto_helper.Credentials()

ec2 = boto.ec2.connect_to_region(c.default_region())
print(ec2.get_all_instances())
