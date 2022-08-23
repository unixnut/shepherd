

import os

from ..utils.cmdline_controller import Handler


extra_options = 'p:'
extra_long_options=['profile=']

cmdline_handler = None


class MyHandler(Handler):
    def __init__(self):
        super(MyHandler, self).__init__()

        # -- defaults --
        self.use_boto = True


    def handle(self, option, opt_arg): 
        if option == "-p" or option == "--profile":
            self.params['profile'] = opt_arg
            return True
        else:
            return False


    def prepare(self):
        """Provide entries to be added to the global state dictionary."""

        # for collecting info to be returned (NOTE: distinct from self.params)
        data = {}

        # -- determine mode --
        env_profile = os.getenv("AWS_DEFAULT_PROFILE")

        # -- choose profile --
        profile = "default"
        if self.params['profile']:
            profile = self.params['profile']
        else:
            if env_profile:
                profile = env_profile

        data['aws_profile'] = profile
        return data



# *** FUNCTIONS ***
def init(controller):
    global cmdline_handler

    cmdline_handler = MyHandler()
    controller.add_handler(cmdline_handler)
    controller.add_options(extra_options)
    controller.add_long_options(extra_long_options)
