#!/usr/bin/env python3
"""jollycron called from crontab
"""

import subprocess
import os
import shutil
import tempfile

# Running on hermes

# TODO get actual assignment names into web form
# Process requests on interval
# Filter bad requests - bad course, bad ass, bad netid
# Filter multiple requests


cwd = os.getcwd()
tempdir = tempfile.mkdtemp(dir='/tmp/', prefix='jolly-')
# tempdir = '/tmp/jolly-5xuo7iq8'
os.chdir(tempdir)

people = 'people.txt'

# copy file
# scp = 'scp -q pisan@homer.u.washington.edu://hw00/d40/pisan/jolly/' + people + ' .'
# os.system(scp)

# if not os.path.isfile(people):
#     print("ERR: Failed to copy file")
#     sys.exit(10)
#
# with open(people) as file:
#     lines = file.readlines()
#
# with open(people, "w") as out:
#     out.write("")

runcmd = ["/home/NETID/pisan/bitbucket/jolly/jolly.py"]
runcmd.append("2018-autumn-CSS-132-A")
runcmd.append("Ass-9")
runcmd.append("hmmorris")
runcmd.append("--download")
runcmd.append("--tdir")
runcmd.append("/home/NETID/pisan/bitbucket/jolly/defaulttests")
runcmd.append("--email")
runcmd.append("--pfile")
runcmd.append("/home/NETID/pisan/private/pass.txt")


try:
    timeout = 60
    run = subprocess.run(runcmd, timeout=timeout)
except subprocess.TimeoutExpired as err:
    alertmsg = format("ALERT: Ran out of time when running %s \n" % runcmd)
    alertmsg = alertmsg + "ALERT: Possible cause waiting for keyboard input\n"
    alertmsg = alertmsg + "ALERT: Possible cause infinite loop\n"
    print(format("Timeout (%s) Expired error: %s" % (timeout, err)))
if not run:
    print(format("ALERT: Did not get to run the command %s " % runcmd))
elif run.returncode != 0:
    print(format("ALERT: Subprocess returned %d for command %s " % (run.returncode, runcmd)))


# move empty file
# scp = 'scp -q ' + people + ' pisan@homer.u.washington.edu://hw00/d40/pisan/jolly/' + people
# os.system(scp)



# counter = 1
# with open('output.txt', 'w') as out:
#     for line in lines:
#         out.write(format("%s. %s" %(counter, line)))
#         counter = counter + 1

# /rc00/d40/pisan/bitbucket/jolly/jolly.py 2018-autumn-CSS-132-A Ass-9 hmmorris
# --download --tdir /rc00/d40/pisan/bitbucket/jolly/


print("Completed: %s" % tempdir)
os.chdir(cwd)
# shutil.rmtree(tempdir)
