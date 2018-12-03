#!/usr/bin/env python3
"""Run the tests in the given directory"""

import argparse
import os
import sys

########################################################################################
# You should not modify this section
# All tests go below to [TESTING AREA]
########################################################################################
PARSER = argparse.ArgumentParser()
PARSER.add_argument("--jollydir")

JOLLYDIR = os.path.abspath(os.path.expanduser(PARSER.parse_args().jollydir))

if not os.path.isdir(JOLLYDIR):
    print("*** %s called with a bad JOLLYDIR directory >%s<: %s" %
          (__file__, JOLLYDIR, " ".join(sys.argv)))
    sys.exit(-1)

sys.path.insert(0, JOLLYDIR)

