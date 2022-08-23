"""Template: NOT USED."""


from ... import cmdline_controller.Handler

extra_options = 'abp:'
extra_long_options=['boto', 'aws-cli', 'profile=']


class MyHandler(Handler):
    def __init__(self):
        super(MyHandler,self).__init__()


    def handle(self, option, opt_arg):
        if ...:
            return True
        else:
            return False


    def prepare(self):
        # for collecting info to be returned (NOTE: distinct from self.params)
        data = {}

        return data


def init(controller):
    controller.add_handler(MyHandler())
    controller.add_options(extra_options)
    controller.add_long_options(extra_long_options)
