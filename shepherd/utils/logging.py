import sys


def report_error(*msg):
    print >> sys.stderr, self + ": Error:", " ".join(msg)


def report_warning(*msg):
    print >> sys.stderr, self + ": Warning:", " ".join(msg)


def report_notice(*msg):
    print >> sys.stderr, self + ": Notice:", " ".join(msg)


def report_info(*msg):
    print >> sys.stderr, self + ": Info:", " ".join(msg)
