

import getopt
from collections import defaultdict

from .. import messages


# *** CLASSES ***
class CommandlineError(RuntimeError):
    pass


class Controller(object):
    """Keeps track of the various cmdline options and handler objects."""

    handlers = []
    allowed_options = ''
    allowed_long_options = []


    def __init__(self, throw=False):
        """@p throw: whether or not to raise an exception instead of exiting in
                     the case of a command line error."""
        self.throw = throw
        pass


    def add_handler(self, handler):
        """Registers a handler."""
        self.handlers.append(handler)


    def add_options(self, options):
        """'options' is a string."""
        self.allowed_options += options


    def add_long_options(self, options):
        """'options' is a list."""
        self.allowed_long_options += options


    # Converts options into a collection of settings
    # Returns (params, args)
    def process_options(self, all_args):
        try:
            optlist, args = getopt.getopt(all_args, self.allowed_options, self.allowed_long_options)
        except getopt.GetoptError as e:
            if self.throw:
                raise CommandlineError(str(e))
            else:
                messages.report_error(e)
                raise SystemExit(1)

        for option, opt_arg in optlist:
            self.process_option(option, opt_arg)

        # Now that options have been processed, get the modules to set internal
        # state, then return collation of information they have collected

        # Create a special dict object that defaults to False for unspecified options
        params = defaultdict(bool)

        for handler in self.handlers:
            params.update(handler.prepare())

        return params, args



    # -- internal methods --
    def process_option(self, option, arg):
        """Keeps trying handlers in order until one has agreed that it has
        handled the option."""
        for handler in self.handlers:
            if handler.handle(option, arg):
                break



class Handler(object):
    def __init__(self):
        # Create a special dict object that defaults to False for unspecified options
        self.params = defaultdict(bool)


    def handle(self, option, arg):
        """Given an option, handle it if necessary and then return True, thus
        preventing other Handler objects from being tried.  Otherwise, if it's
        not handled, return False."""
        return False


    def prepare(self):
        """Perform any preparations once options have been handled.  Return any
        data that is to be collated by Controller."""
        return {}
