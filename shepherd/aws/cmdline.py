from __future__ import absolute_import

import os

from ..utils.cmdline_controller import Handler


extra_options = 'abp:'
extra_long_options=['boto', 'aws-cli', 'profile=']

cmdline_handler = None


class MyHandler(Handler):
    def __init__(self):
        super(MyHandler,self).__init__()

        # -- defaults --
        self.use_boto = True


    def handle(self, option, opt_arg): 
        if option == "-a" or option == "--aws-cli":
            self.use_boto = False
            return True
        elif option == "-b" or option == "--boto":
            self.params["force_boto"] = True
            return True
        elif option == "-p" or option == "--profile":
            self.params["profile"] = opt_arg
            return True
        else:
            return False


    def prepare(self):
        # for collecting info to be returned (NOTE: distinct from self.params)
        data = {}

        # -- determine mode --
        # This is either boto or aws-cli, and is reflected in use_boto (as a flag)
        env_profile = os.getenv("AWS_DEFAULT_PROFILE")
        if env_profile:
            # treat this as a weak preference for aws-cli
            if not self.params["force_boto"]:
                self.use_boto = False

        # -- choose profile --
        profile = "default"
        if self.params["profile"]:
            profile = self.params["profile"]
        else:
            if env_profile and not self.use_boto:
                profile = env_profile
        
        data['use_boto'] = self.use_boto
        data['profile'] = profile
        return data



# *** FUNCTIONS ***
def init(controller):
    global cmdline_handler

    cmdline_handler = MyHandler()
    controller.add_handler(cmdline_handler)
    controller.add_options(extra_options)
    controller.add_long_options(extra_long_options)
