#! /usr/bin/python
# shepherd (Python script) -- Control cloud servers using the provider's API
#
__version__ = '2.0.4'
# Copyright: (c)2015 Alastair Irvine <alastair@plug.org.au>
# Keywords:  aws boto virsh
# Licence:   This file is released under the GNU General Public License
'''Description:
  Like virsh, this script controls servers "externally", i.e. not by logging
  into them like ansible does.  However, it interoperates with ansible by
  using its inventory file; see http://docs.ansible.com/intro_inventory.html .

Usage: shepherd [ -i <inventory> ] <host-pattern> [ start | stop | restart | kill ]
Options:
  -i <inventory>, --inventory-file=<inventory>   Specify inventory host file
                                                 (default=/etc/ansible/hosts)
  -y, --confirm                                  Confirm termination of instances
  -n, --dry_run                                  Tell boto not to perform the action
  -w, --poll                                     Wait until operation is complete
  -s <seconds>, --interval=<seconds>             Activate -w and set the interval
  -R, --running                                  Only show running instances
  -S, --stopped                                  Only show stopped instances
  -q, --quiet                                    Don't show useful messages
  -v                                             Show progress when polling
'''
# Licence details:
#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or (at
#     your option) any later version.
#
#     See http://www.gnu.org/licenses/gpl-2.0.html for more information.
#
#     You can find the complete text of the GPLv2 in the file
#     /usr/share/common-licenses/GPL-2 on Debian systems.
#     Or see the file COPYING in the same directory as this program.
#
#
# TO-DO:
#   + handle hosts not in in primary region
#   + go(): create PerRegionCohort objects before taking action
#   + detect invalid action names


import sys
import socket        # for gaierror
import logging

## from . import ...
from .utils import messages
from .utils.cmdline_controller import Controller

from . import cmdline as global_cmdline
from .aws import cmdline as aws_cmdline
from . import inventory
from . import errors


messages.self = 'shepherd'

## __all__ = ...

## AWS_DEFAULT_REGION
# boto.connect_ec2() uses default region from env/config, or "us-east-1" if none was specified,


# *** CLASSES ***


# *** FUNCTIONS ***
# Returns: action, host_pattern, params
def process_cmdline(all_args):
    global params

    controller = Controller()

    # init global options
    global_cmdline.init(controller)
    # then run through all provider modules' cmdline sub-sub-modules
    aws_cmdline.init(controller)

    # creation of params is only one of the things this does
    params, args = controller.process_options(all_args)

    # handle the rest of the args present after the options
    action, host_pattern = global_cmdline.process_args(args)

    return action, host_pattern, params


def go(action, host_maps, params):
    # For each provider, this will hold a reference to the module and
    # per-region info used to track the group of hosts being acted upon
    provider_info = {}

    for provider in host_maps:
        provider_info[provider] = {}
        try:
            # do a relative import of the submodule for this provider
            # (no need to use fromlist=[provider])
            provider_info[provider]['module'] = __import__(provider, globals=globals(), level=1)
            provider_info[provider]['module'].init(params)
        except ImportError as e:
            raise errors.ProviderError("Unknown provider " + provider)

        # take action
        for region in host_maps[provider]:
            assert region != 'module'

            # Show a region & provider summary line between cohhorts
            if action == "status" and params['verbose'] >= 1:
                print(region, "(" + provider + ")")

            ids = [id for id in host_maps[provider][region]]
            if ids:
                provider_info[provider][region] = \
                  provider_info[provider]['module'].PerRegionCohort(region, ids, \
                                                      host_maps[provider][region], params)

                # Show a summary for actions other than status
                if action != "status" and action != 'fullstatus' and params['verbose'] >= 1:
                    print("Running %s on instances in region %s (%s):\n  " % (action, region, provider), ", ".join(ids))
                provider_info[provider][region].take_action(action)
            else:
                # This shouldn't happen because the map for that provider
                # or region won't have been created by inventory.collate()
                messages.report_notice("No hosts had correct cloud info");

    return provider_info


def poll(host_maps, provider_info, params):
    import time

    if params['debug']:
        print("Polling every %d seconds, up to %d times" % (params['poll_interval'], params['max_poll']))

    iterations = 0
    while iterations < params['max_poll']:
        undesired_count = 0
        for provider in host_maps:
            for region in host_maps[provider]:
                cohort = provider_info[provider][region]
                undesired_count += cohort.num_deviants(iterations == 0)
        if undesired_count == 0:
            break
        else:
            time.sleep(params['poll_interval'])

        if params['verbose'] >= 2:
            # Show a line of progress dots.  Don't use 'print' because it adds a space.
            sys.stdout.write(".")
            sys.stdout.flush()
        iterations += 1

        # TO-DO: optionally relist

    # newline for the dots that were printed
    if params['verbose'] >= 2:
        if iterations == 0:
            print("No action required.")
        else:
            if undesired_count == 0:
                print(" Complete.")
            else:
                print(" Giving up.")


def main():
    """Acts like main() in a C program.  Return value is used as program exit code."""

    try:
        action, host_pattern, params = process_cmdline(sys.argv[1:])
    except errors.CommandlineError as e:
        messages.report_error(str(e))
        global_cmdline.show_help(sys.stderr)
        return 1

    # self.params['verbose'] governs logging within the program, but
    # self.params['debug'] governs the root logger
    if params['debug'] >= 2:
        global_loglevel = logging.DEBUG
    elif params['debug'] >= 1:
        global_loglevel = logging.INFO
    else:
        global_loglevel = logging.WARNING
    if params['logfile']:
        logging.basicConfig(level=global_loglevel, filename=self.params['logfile'])
    else:
        logging.basicConfig(level=global_loglevel)

    if params['verbose'] >= 3:
        loglevel = logging.DEBUG
    elif params['verbose'] >= 2:
        loglevel = logging.INFO
    elif params['verbose'] >= 1:
        loglevel = logging.WARNING
    else:
        loglevel = logging.ERROR
    params['logger'] = logging.getLogger("shepherd")
    params['logger'].setLevel(loglevel)

    try:
        host_maps = inventory.collate(host_pattern, 
                                      params['inventory_filename'],
                                      params['logger'])
    except inventory.NoHostsError as e:
        messages.report_notice("No instances matched");
        return 0
    except inventory.InventoryFileMissing as e:
        messages.report_error(str(e))
        return 7
    except inventory.InventoryError as e:
        messages.report_error(str(e))
        return 6

    try:
        provider_info = go(action, host_maps, params)

        if params['poll'] and action != "status" and not params['dry_run']:
            poll(host_maps, provider_info, params)
    except errors.ProviderError as e:
        messages.report_error(str(e))
        return 5
    except errors.AuthError as e:
        messages.report_error(str(e) + ": check ~/.aws/credentials, or use appropriate option")
        return 10
    except errors.ActionError as e:
        messages.report_error(str(e))
        global_cmdline.show_help(sys.stderr)
        return 1
    except errors.MissingInstanceError as e:
        # Error already reported
        return 3
    except errors.InstanceError as e:
        messages.report_error(str(e))
        return 4
    except socket.gaierror as e:
        messages.report_error("Can't connect to endpoint: " + str(e))
        return 8


def action_debug(all_args):
    try:
        action, host_pattern, params = process_cmdline(all_args)
        print("action:", action, "host_pattern:", host_pattern)
        print("profile:", params['profile'])
    except SystemExit as e:
        print("(exiting with exit code %d)" % e.code)
    ## except RuntimeError, e:


# *** MAINLINE ***
# See __main__.py
# (Invoke with "python -m shepherd" under Python 2.7+, otherwise
# "python -m shepherd.__main__")
