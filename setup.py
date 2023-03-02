#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages


requirements = [## 'ansible>=2.7.5',
                'boto3',
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
    entry_points={
        'console_scripts': [
            'shepherd=shepherd:main',
        ],
    },
    url='https://github.com/unixnut/shepherd',
    install_requires=requirements,
    setup_requires=setup_requirements,
    keywords="aws ec2 cli",
    packages=find_packages(".", exclude=['tests']),
    version="2.0.5",
    zip_safe=False,
    license="GNU General Public License v3",
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Environment :: Console',
        'Topic :: Utilities',
        'Operating System :: POSIX :: Linux',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Unix Shell',
    ],
)
