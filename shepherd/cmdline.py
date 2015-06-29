from __future__ import absolute_import

import sys
import os

from .utils.cmdline_controller import Handler as Handler
from .utils import logging
from . import __doc__ as program_docstring
from . import errors


basic_options='hdi:ynws:m:RSvq'
basic_long_options=['help', 'inventory-file=', 'confirm', 'dry-run', 'quiet',
                    'poll', 'interval=', 'max-poll=',
                    'running', 'stopped']

# -- action stuff --
# roughly mimic the commands supported by service(8)
allowed_actions = ('status', 'start', 'restart', 'stop', 'kill')

# translate other action sets into the above
virsh_actions = {'list': 'status', 'dominfo': 'status', 'start': 'start', 'reboot': 'restart', 'shutdown': 'stop', 'destroy': 'kill'}
aws_actions = {'start': 'start', 'reboot': 'restart', 'stop': 'stop', 'terminate': 'kill'}

cmdline_handler = None


# *** CLASSES ***
class MyHandler(Handler):
    def __init__(self):
        super(MyHandler,self).__init__()

        # -- defaults --
        self.params['debug'] = 0
        self.params['verbose'] = 1
        self.params['poll_interval'] = 5
        self.params['max_poll'] = 20
        self.params['inventory_filename'] = os.getenv('ANSIBLE_HOSTS', "/etc/ansible/hosts")


    def handle(self, option, opt_arg): 
        if option == "-i" or option == "--inventory-file":
            self.params['inventory_filename'] = opt_arg
        elif option == "-y" or option == "--confirm":
            self.params['confirm'] = True
        elif option == "-w" or option == "--poll":
            self.params['poll'] = True
        elif option == "-s" or option == "--interval":
            self.params['poll'] = True
            self.params['poll_interval'] = int(opt_arg)
            ## if self.params['debug']:
            ##     print opt_arg
        elif option == "-m" or option == "--max-poll":
            self.params['poll'] = True
            self.params['max_poll'] = int(opt_arg)
        elif option == "-n" or option == "--dry-run":
            self.params['dry_run'] = True
        elif option == "-R" or option == "--running":
            self.params['only_running'] = True
        elif option == "-S" or option == "--stopped":
            self.params['only_stopped'] = True
        elif option == "-v":
            self.params['verbose'] += 1
        elif option == "-q" or option == "--quiet":
            self.params['verbose'] -= 1
        elif option == "-d":
            self.params['debug'] += 1
        elif option == "-h" or option == "--help":
            show_help()
            sys.exit(0)
        else:
            return False

        return True


    def prepare(self):
        return self.params



# *** FUNCTIONS ***
def show_help(dest=sys.stdout):
    print >> dest, program_docstring,



def init(controller):
    global cmdline_handler

    cmdline_handler = MyHandler()
    controller.add_handler(cmdline_handler)
    controller.add_options(basic_options)
    controller.add_long_options(basic_long_options)


def process_args(args):
    # -- argument checking and handling--
    if args == ['list']:
        action = 'status'
        host_pattern = "all"
    else:
        ## print len(args), '[' + "; ".join(args) + ']'
        if len(args) == 2:
            # check for reversed order with virsh action names
            if args[0] in virsh_actions:
                action = virsh_actions[args[0]]
                host_pattern = args[1]
            elif args[0] in aws_actions:
                # ...and AWS
                action = aws_actions[args[0]]
                host_pattern = args[1]
            else:
                action = args[1]
                host_pattern = args[0]
        else:
            raise errors.CommandlineError("Invalid command-line parameters.")

    return action, host_pattern
