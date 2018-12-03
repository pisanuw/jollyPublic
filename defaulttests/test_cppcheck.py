#!/usr/bin/env python3
"""Run cppcheck - A tool for static C/C++ code analysis
cppcheck
"""

import jollytesthelper
import jolly

allcpps = jolly.Jolly.dir_list(".*cpp$")
allhs = jolly.Jolly.dir_list(".*h$")
allimps = allcpps + allhs


cppcheckflags = "--enable=all,--inconclusive,--language=c++,--std=posix,--suppress=missingIncludeSystem".split(',')


jolly.Jolly.run_test("cppcheck", cppcheckflags, allimps)
