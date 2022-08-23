

import sys


def report_error(*msg):
    print(self + ": Error:", " ".join(msg), file=sys.stderr)


def report_warning(*msg):
    print(self + ": Warning:", " ".join(msg), file=sys.stderr)


def report_notice(*msg):
    print(self + ": Notice:", " ".join(msg), file=sys.stderr)


def report_info(*msg):
    print(self + ": Info:", " ".join(msg), file=sys.stderr)
