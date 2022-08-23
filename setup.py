#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages


requirements = [## 'ansible>=2.7.5',
                'boto3',
                'awscli' # this is just used to get the environment variables that aws-cli uses
               ] ## ['Click>=6.0', ]

setup_requirements = ['pytest-runner', 'bumpversion', 'setuptools~=40.4.3', 'wheel']

with open('README.md') as readme_file:
    readme = readme_file.read()

setup(
    name="cloud-shepherd",
    author="Alastair Irvine",
    description="Control cloud servers using the provider's API",
    long_description=readme,
    long_description_content_type='text/markdown',
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
    version="2.0.0",   # TO-DO: use 'bumpversion'
    zip_safe=False,
)
