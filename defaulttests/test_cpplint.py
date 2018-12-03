#!/usr/bin/env python3
"""Run cpplint
The style guidelines this tries to follow are those in
https://google.github.io/styleguide/cppguide.html
https://github.com/google/styleguide/tree/gh-pages/cpplint
cpplint
"""

import jollytesthelper
import jolly

allcpps = jolly.Jolly.dir_list(".*cpp$")
allhs = jolly.Jolly.dir_list(".*h$")
allimps = allcpps + allhs

flags = ["--verbose=0",
         "--filter=-legal/copyright,-whitespace/tab,-build/namespaces,-build/include,-build/header_guard,-whitespace/newline,-whitespace/braces,-build/c++11,-runtime/threadsafe_fn"""
         ]

# exit code will not be zero if any errors found, so don't print an error message for that
jolly.Jolly.run_test("cpplint", flags, allimps, True)
