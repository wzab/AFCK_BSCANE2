#!/usr/bin/python
import rlcompleter
import readline
readline.parse_and_bind("tab: complete")
import os
#histfile=os.path.join(os.environ["HOME"],".pyhist.cb")
histfile="./.pyhist.i2c"
try:
    readline.read_history_file(histfile)
except IOError:
    pass
import atexit
atexit.register(readline.write_history_file, histfile)
del os,histfile
from AFCK_tools import *

SiSetFrq(156250000)
ClkMtx_set_out(15,4)
ClkMtx_set_out(15,5)
ClkMtx_set_out(15,6)
