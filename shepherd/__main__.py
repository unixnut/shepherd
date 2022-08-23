#! /usr/bin/python
"""Universal package entry point.

Determines the name of the package this file resides in, imports it and runs
its main() function.  Assumes the package dir's parent is in the module path.

Usage: python -m <package_name>
   or: python -m <package_name>.__main__

Note: the former only works under Python 2.7+

The method used by this script is similar to the method suggested by
https://www.python.org/dev/peps/pep-0299/ in that sys.argv is passed to main()
and its return value is used as the program exit code."""
 


import sys
from os.path import dirname, basename, splitext, realpath, exists, islink


# *** FUNCTIONS ***
def robust_import(package_name, filename):
    """Tries to dynamically import a package and if it fails, adds the
    package's parent dir to the module path and try again.  

    @param filename: a file in the package dir
    @return a reference to the imported package"""
    try:
        # assume this file's parent dir (and thereby that of the package)
        # is already present in sys.path
        return __import__(package_name) 
    except ImportError as e:
        # Scenario 1b: script is being run in-place manually
        #
        # We can add the package's parent dir to sys.path and retry the import
        sys.path.insert(0, dirname(dirname(filename)))
        ## print sys.path[0]
        return __import__(package_name) 


# *** MAINLINE ***
try:
    # -- Check how this script is being run --
    if basename(__file__) == "__main__.py":
        # Scenario 1: script is being run in-place (either via "python -m" or manually)
        #
        # Note: relative imports can't be used in non-package, i.e this script
        package_name = basename(dirname(__file__))
        package = robust_import(package_name, __file__)
    else:
        # Otherwise, assume __main__.py has been copied or symlinked
        # elsewhere and therefore is being run under another name

        # -- Test for symlinking --
        # It's OK to use islink() because it's irrelevant if the file
        # itself is not a symlink, but a directory along the path is
        if islink(__file__):
            ## exists(dirname(realpath(__file__)) + "__init__.py"): 

            # Scenario 2: script is symlinked
            #
            # Use the directory of the file that the script points to to
            # determine the package name
            package_name = basename(dirname(realpath(__file__)))
            ## print package_name
            package = robust_import(package_name, realpath(__file__))
        else:
            # Scenario 3: script is a copy of__main__.py
            # 
            # Use the filename as a guess for the package name and hope that
            # the package dir's parent is in the module path already, because
            # there is no way to determine it programatically
            package_name, ext = splitext(basename(__file__))
            package = __import__(package_name) 
except ImportError as e:
    # If the top-level import failed, be polite
    if str(e) == "No module named " + package_name:
        print("%s: Error: Can't find package '%s'" % (__file__, package_name),
              file=sys.stderr)
        sys.exit(99)
    else:
        # Otherwise it's a coding error or dependency failure
        raise

if __name__ == '__main__':
    # Note difference from https://www.python.org/dev/peps/pep-0299/:
    #   main() is used, not __main__()
    # Note: argv is passed verbatim, including argv[0]
    sys.exit(package.main(sys.argv))
