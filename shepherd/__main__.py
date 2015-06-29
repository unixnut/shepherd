"""Universal package entry point.

Determines the name of the package this file resides in, imports it and runs
its main() function.

This is similar to the method suggested by
https://www.python.org/dev/peps/pep-0299/ in that sys.argv is passed to main()
and its return value is used as the program exit code."""
 
import sys
from os.path import realpath, dirname, basename

# Determine name of package and import it.
# Note: relative imports can't be used in non-package, but this is a non-issue
# because this file's dir, and thereby that of the package dir has been put
# into sys.path automatically
package_name = basename(dirname(realpath(__file__)))
package = __import__(package_name) 

if __name__ == '__main__':
    # Note difference from https://www.python.org/dev/peps/pep-0299/:
    #   main() is used, not __main__()
    # Note: argv is passed verbatim, including argv[0]
    sys.exit(package.main(sys.argv))
