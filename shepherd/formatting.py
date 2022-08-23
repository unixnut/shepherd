



def print_host(name, id, state, msg=None, indent = "  "):
    """msg, if present, is printed (with a two-space indent) after the normal
    line."""
    print("%-24s %-25s %s" % (name, id, state))
    if msg:
        print(indent + ("\n" + indent).join(msg.split("\n")))
