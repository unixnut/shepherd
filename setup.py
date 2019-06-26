#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages


requirements = [## 'ansible>=2.7.5',
                'botocore', 'boto',
                'awscli' # this is just used to get the environment variables that aws-cli uses
               ] ## ['Click>=6.0', ]

setup_requirements = ['pytest-runner', 'bumpversion', 'setuptools~=40.4.3', 'wheel']


setup(
    name="shepherd",
    author="Alastair Irvine",
    description="Control cloud servers using the provider's API",
##     entry_points={
##         'console_scripts': [
##             'hashpw=shepherd:main',
##         ],
##     },
    scripts=['bin/shepherd'],
    url='https://github.com/unixnut/cloud-support',
    install_requires=requirements,
    setup_requires=setup_requirements,
    keywords="aws ec2 cli",
    packages=find_packages(".", exclude=['tests']),
    version="1.3.0",
    zip_safe=False,
)
