#!/usr/bin/env python3
"""Run the tests in the given directory"""

import jollytesthelper
import jolly

allcpps = jolly.Jolly.dir_list(".*cpp$")
allhs = jolly.Jolly.dir_list(".*h$")
allimps = allcpps + allhs

# compile and run CPPCOMPILER CPPFLAGS
jolly.Jolly.cpp_compile_run(allcpps)

# cleanup for C++
jolly.Jolly.c_clean_exe_files()
