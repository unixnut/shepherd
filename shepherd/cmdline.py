"""Global command-line parsing module."""


import sys
import os
import re

from .utils.cmdline_controller import Handler as Handler
from . import __doc__ as program_docstring
from . import errors


basic_options='hdi:ynws:m:RSvq'
basic_long_options=['help', 'inventory-file=', 'confirm', 'dry-run', 'quiet',
                    'poll', 'interval=', 'max-poll=',
                    'running', 'stopped']

# -- action stuff --
# roughly mimic the commands supported by service(8)
allowed_actions = ('status', 'fullstatus', 'start', 'restart', 'stop', 'kill')

# translate other action sets into the above
virsh_actions = {'list': 'status', 'dominfo': 'fullstatus', 'start': 'start', 'reboot': 'restart', 'shutdown': 'stop', 'destroy': 'kill'}
aws_actions = {'start': 'start', 'reboot': 'restart', 'stop': 'stop', 'terminate': 'kill'}
vagrant_actions = {'up': 'start', 'reload': 'restart', 'halt': 'stop', 'destroy': 'kill'}
other_actions = {'delete': 'kill', 'show': 'fullstatus'}

cmdline_handler = None


# *** CLASSES ***
class NotFoundException(Exception):
    pass



class MyHandler(Handler):
    def __init__(self):
        super(MyHandler, self).__init__()

        # -- defaults --
        self.params['debug'] = 0
        self.params['verbose'] = 1
        self.params['poll_interval'] = 5
        self.params['max_poll'] = 20
        self.params['inventory_filename'] = os.getenv('ANSIBLE_INVENTORY',
                                                      os.getenv('ANSIBLE_HOSTS',
                                                                "/etc/ansible/hosts"))
        self.params['logfile'] = None


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
            raise SystemExit(0)
        else:
            return False

        return True


    def prepare(self):
        return self.params



# *** FUNCTIONS ***
def show_help(dest=sys.stdout):
    print(program_docstring, end='', file=dest)



def init(controller):
    global cmdline_handler

    cmdline_handler = MyHandler()
    controller.add_handler(cmdline_handler)
    controller.add_options(basic_options)
    controller.add_long_options(basic_long_options)


def lookup_action(name, *lists):
    for l in lists:
        if name in l:
            return l[name]
    raise NotFoundException("Not found in any list")


def process_args(args):
    # -- argument checking and handling--
    # special case for virsh emulation
    if args == ['list']:
        action = 'status'
        host_pattern = "all"
    else:
        ## print len(args), '[' + "; ".join(args) + ']'
        if len(args) == 2:
            # check for reversed order with virsh/AWS/other action name
            try:
                action = lookup_action(args[0], virsh_actions, aws_actions, vagrant_actions, other_actions)
                host_list = [args[1]]
            except NotFoundException as e:
                # check for reversed order with standard action name
                if args[0] in allowed_actions:
                    action = args[0]
                    host_list = args[1:]
                else:
                    # otherwise it's service(8) order
                    action = args[1]
                    host_list = [args[0]]
        elif len(args) > 2:
            host_list = args[1:]
            try:
                action = lookup_action(args[0], virsh_actions, aws_actions, vagrant_actions, other_actions)
            except NotFoundException as e:
                action = args[0]
        else:
            raise errors.CommandlineError("Invalid command-line arguments.")

        # Join all the remaining args together (maybe several hosts per arg), separated
        # by spaces, then covert to a colon-separated string of hosts
        s = " ".join(host_list)
        host_pattern = re.sub(r"[\s:,]+", ":", s)

    return action, host_pattern
