#!/usr/bin/env python3
"""Run the tests in the given directory"""

import datetime
import os
import shutil
import subprocess

import jollyhelper


# runtests(args.course_name, args.assignment_name, args.netid, args.testdir)
class Runner:
    # pylint: disable-msg=too-many-arguments
    def __init__(self, canvas, netids, assdir, testdir, testfileprefix, testlog):
        self.canvas = canvas
        self.netids = netids
        self.assdir = assdir
        self.testdir = testdir
        self.testfileprefix = testfileprefix
        self.testlog = testlog

    # pylint: enable-msg=too-many-arguments
    def logit(self, string):
        with open(self.testlog, "a") as outfile:
            outfile.write(string)

    def run_test(self, cmd, args=None, timeout=10):
        # if there is a local file or full path given, let it override the directory
        if os.path.isfile(cmd):
            fullcmd = cmd
        else:
            fullcmd = os.path.join(jollyhelper.JH.get("testerpath"), cmd)
        if not os.path.isfile(fullcmd):
            print("*** Could not find %s to execute, skipping test" % fullcmd)
            return False
        if not os.access(fullcmd, os.X_OK):
            print("*** Cannot execute %s, check file permissions" % fullcmd)
            return False
        # print("Running %s" % fullcmd, flush=True)
        if not args:
            args = ['--jollydir', os.path.dirname(os.path.realpath(__file__))]
        runcmd = [fullcmd] + args
        # print("Running: %s " % runcmd)
        run = None
        with open(self.testlog, "a") as outfile:
            try:
                outfile.flush()
                timeout = int(timeout)
                run = subprocess.run(runcmd, stdout=outfile, stderr=outfile, timeout=timeout)
                outfile.flush()
            except subprocess.TimeoutExpired as err:
                alertmsg = format("ALERT: Ran out of time when running %s \n" % fullcmd)
                alertmsg = alertmsg + "ALERT: Possible cause waiting for keyboard input\n"
                alertmsg = alertmsg + "ALERT: Possible cause infinite loop\n"
                outfile.write(alertmsg)
                print(alertmsg)
                print(format("Timeout (%s) Expired error: %s" % (timeout, err)))
            if not run:
                print(format("ALERT: Did not get to run the command %s " % fullcmd))
            elif run.returncode != 0:
                print(format("ALERT: Subprocess returned %d for command %s " % (run.returncode, fullcmd)))
        return run

    def run_all_tests(self):
        alltestfiles = os.listdir(self.testdir)
        testfiles = []
        for testfile in alltestfiles:
            for prefix in self.testfileprefix.split(','):
                if testfile.startswith(prefix):
                    testfiles.append(testfile)
                    break
        print("Test files found are: ", testfiles)
        for netid in self.netids:
            dfull = os.path.join(self.assdir, netid)
            if not os.path.isfile(os.path.join(dfull, "jolly_downloaded.txt")):
                continue
            os.chdir(dfull)
            if os.path.isfile(self.testlog):
                os.remove(self.testlog)
            print("Looking at %s" % netid)
            test_start_time = format("Starting tests: %s\n" % str(datetime.datetime.now()))
            self.logit(test_start_time)
            for tesfile in testfiles:
                testfilefull = os.path.join(self.testdir, tesfile)
                if not os.access(testfilefull, os.X_OK):
                    print("ALERT: testfile is not executable %s " % testfilefull)
                    continue
                # each test opens the file to append
                result = self.run_test(testfilefull, timeout=int(jollyhelper.JH.get("timeout")))
                if not result:
                    print("\t[Failed] %s" % testfilefull)
                else:
                    try:
                        if result.returncode == 0:
                            print("\t[Success] %s" % testfilefull)
                        else:
                            print("\t[Success with return value %s] %s" % (result.returncode, testfilefull))
                    except AttributeError:
                        print("\t[??? got %s] %s" % (result, testfilefull))
                # in case the test changed current directory
                os.chdir(dfull)
            # Finished all tests, record time
            testend_time = format("Finished tests: %s\n\n\n" % str(datetime.datetime.now()))
            self.logit(testend_time)
            if os.path.isfile(self.testlog):
                toemailfile = os.path.join(dfull, "jolly_toemail.txt")
                shutil.copyfile(self.testlog, toemailfile)
