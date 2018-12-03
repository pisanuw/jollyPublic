#!/usr/bin/env python3
"""jolly is the driver for downloading files from Canvas
"""

import argparse
from argparse import RawTextHelpFormatter
import getpass
import os
import re
import shutil

import jollycanvashelper
import jollyhelper
import jollyrunner


# pylint: disable-msg=too-many-instance-attributes
class Jolly:
    # static variables
    testdir = None
    list_files = jollyhelper.list_files
    cpp_compile_run = jollyhelper.cpp_compile_run
    insert_file_at_end = jollyhelper.insert_file_at_end
    c_clean_exe_files = jollyhelper.c_clean_exe_files
    dir_list = jollyhelper.dir_list

    @staticmethod
    def run_test(vmrunner, vmflags, files, suppress=False, pattern=None):
        print("", flush=True)
        result = jollyhelper.generic_run_short(vmrunner, vmflags + files, suppress, pattern)
        print("", flush=True)
        return result

    @staticmethod
    def check_required_files(required_files):
        have_allrequiredfiles = True
        for file in required_files:
            if os.path.isfile(file):
                print("OK: Found submission file %s" % file)
            else:
                print("ERR: Could not find file %s" % file)
                have_allrequiredfiles = False
        return have_allrequiredfiles

    @staticmethod
    def set_test_directory(newdir):
        Jolly.testdir = newdir

    @staticmethod
    def check_test_dir():
        if not Jolly.testdir:
            print("TESTERR: Must use \'jolly.Jolly.setTestDirectory(os.path.dirname(os.path.realpath(__file__)))\' \
                  \nin the test file before using any jolly helper functions")
            return False
        return True

    @staticmethod
    def get_test_file(file):
        if Jolly.check_test_dir():
            return os.path.join(Jolly.testdir, file)
        return None

    @staticmethod
    def copy_file_to_student_directory(file):
        if not Jolly.check_test_dir():
            return
        fullfile = os.path.join(Jolly.testdir, file)
        if not os.path.isfile(fullfile):
            print("TESTERR: Could not find %s to copy" % fullfile)
            return
        shutil.copy(fullfile, os.getcwd())

    @staticmethod
    # assumimng current directory is ../ass/netid
    def get_student_netid():
        cwd = os.getcwd()
        (_, netid) = os.path.split(cwd)
        return netid

    # pylint: disable-msg=too-many-arguments
    def __init__(self, course_name, ass_name, netids_given, createempty=False, helpmsg=""):
        self.course_name = course_name
        self.ass_name = ass_name
        self.netids = [] if not netids_given else netids_given.split(',')
        self.mycourse = None
        self.myass = None
        self.myusers = None
        self.createempty = createempty
        self.helpmsg = helpmsg
        self.canvas = jollycanvashelper.Canvas()
        self.file_toemail = jollyhelper.JH.get("emailfile")
        self.file_toattach = jollyhelper.JH.get("emailattach")

    # pylint: enable-msg=too-many-arguments
    def setup(self):
        return self.canvas.get_courses() and self.download_course_ass_user_info()

    def send_emails(self, asspath, emailsubject, passwordfile):
        """no password, interactive or password from file"""
        if not passwordfile:
            password = None
        elif passwordfile == '-':
            print("Need to authenticate %s with SMTP server using password" % getpass.getuser())
            password = getpass.unix_getpass("Enter password: ")
        else:
            # check authfile
            authfile = os.path.abspath(os.path.expanduser(passwordfile))
            if not os.path.isfile(authfile):
                print("ERR: password file %s could not be found" % authfile)
                return
            with open(authfile) as authfp:
                password = authfp.readline().rstrip()
        for netid in self.netids:
            userdir = os.path.join(asspath, netid)
            os.chdir(userdir)
            # will get netid from file
            jollyhelper.mail_send_file(subject=emailsubject,
                                       filetosend=self.file_toemail,
                                       filetoattach=self.file_toattach,
                                       password=password, reallysend=True)

    def download(self):
        return self.setup() and \
               self.canvas.download(self.mycourse, self.myass, self.myusers, self.createempty)

        # pylint: disable-msg=too-many-arguments

    def run(self, download, tdir, tprefix, unzip, email, emailsubject, passwordfile):
        if not self.course_name and not download:
            print(self.helpmsg)
            print("ERR: Use 'jolly --download' to get a list of courses")
            return
        if download:
            if not self.download():
                return
        if not self.ass_name:
            print(self.helpmsg)
            print("ERR: Cannot download, unzip or email if no assignment name is given")
            print("ERR: Specify --download to get a list of assignments")
            return
        if not download and not tdir and not unzip and not email:
            print("ERR: Not downloading, testing or emailing, so what are we doing?")
            print("ERR: Specify --download, then --unzip then --tdir and finally --email")
            return
        asspath = os.path.abspath(jollyhelper.sanitize_string(self.ass_name))
        if not self.netids:
            self.netids = jollyhelper.get_netids_from_directory(asspath)
        if not os.path.isdir(asspath):
            print("ERR: Assignment directory %s not found, did you download it?" % asspath)
            return
        if unzip:
            jollyhelper.unzip_files_for_assignment(self.ass_name, self.netids)
        if tdir is not None:
            self.run_tests(tdir, tprefix)
        if email:
            if not emailsubject:
                emailsubject = format("%s - %s - %s"
                                      % (self.course_name, self.ass_name, jollyhelper.JH.get("emailsubject")))
            self.send_emails(asspath, emailsubject, passwordfile)

    def run_tests(self, testdir, testfileprefix):
        if not testdir or not os.path.isdir(testdir):
            print("ERR: The test directory %s is not valid" % testdir)
            return False
        testdir = os.path.abspath(testdir)
        asspath = os.path.abspath(jollyhelper.sanitize_string(self.ass_name))
        if not os.path.isdir(asspath):
            print("ERR: The assignment directory %s is not valid" % asspath)
            return False
        # we could be only testing, so no userlist needed if testing single netid
        allnetids = jollyhelper.get_netids_from_directory(asspath)
        netids = self.netids
        if not self.netids:
            if not self.course_name:
                print("ERR: Cannot test if no course name is given")
                return False
            netids = allnetids
        filtered_netids = []
        for nid in netids:
            if nid not in allnetids:
                print("ERR: Cannot find directory for %s" % nid)
            else:
                filtered_netids.append(nid)
        if not filtered_netids:
            return False
        runner = jollyrunner.Runner(self.canvas, filtered_netids, asspath, testdir, testfileprefix,
                                    self.canvas.logfilename)
        runner.run_all_tests()
        return True

    def check_course_name_pattern(self):
        if self.course_name in self.canvas.AllCourses:
            return self.course_name
        if not self.course_name:
            return None
        matches = []
        pattern = ".*" + self.course_name + ".*"
        for course in self.canvas.AllCourses:
            if re.match(pattern, course):
                matches.append(course)
        if len(matches) == 1:
            return matches[0]
        return None

    def download_courses(self):
        if not self.course_name:
            print(self.helpmsg)
            courses = self.canvas.list_courses()
            print("\nSpecify a course name")
            print("try: jolly COURSENAME --download")
            if courses:
                print("try: jolly %s --download" % courses[0][0])
            return None
        possible_course = self.check_course_name_pattern()
        if not possible_course:
            self.canvas.list_courses()
            print("ERR: Could not find course %s" % self.course_name)
            return None
        self.course_name = possible_course
        self.mycourse = self.canvas.get_course(self.course_name)
        return self.mycourse

    def check_download_ass(self):
        if not self.ass_name:
            assignments = self.mycourse.list_assignments()
            print("\nSpecify an assignment")
            print("try: jolly %s ASSIGNMENT --download" % self.course_name)
            if assignments:
                print("try: jolly %s '%s' --download" % (self.course_name, assignments[0]))
            return None
        self.myass = self.mycourse.find_download_assignment(self.ass_name)
        if not self.myass:
            self.mycourse.list_assignments()
            print("ERR: Could not find assignment %s" % self.ass_name)
            return None
        return self.myass

    def download_course_ass_user_info(self):
        if not self.download_courses() or \
                not self.mycourse.download_assignments() or \
                not self.check_download_ass():
            return False
        self.mycourse.get_users()
        self.myusers = {}
        self.mycourse.get_submissions(self.myass)
        if not self.netids:
            self.myusers = self.mycourse.users_by_canvas_id
            self.netids = self.mycourse.get_netids()
        else:
            filtered_netids = []
            for nid in self.netids:
                user = self.mycourse.get_user_by_netid(nid)
                if not user:
                    print("ERR: Could not find user %s" % nid)
                    continue
                self.myusers[user.canvasid] = user
                filtered_netids.append(nid)
            self.netids = filtered_netids
            if not self.netids:
                self.mycourse.list_users()
                return False
        return True

    # @staticmethod
    # def mailSendFile(subject='Comments from JollyFeedback Automated Script',
    #                  fromname=None,
    #                  reallysend=False):
    #     print("inside jolly")
    #     jollyhelper.mailSendFile(subject=subject, fromname=fromname, reallysend=reallysend)


def main_entry():
    parser = argparse.ArgumentParser(
        formatter_class=RawTextHelpFormatter,
        prog='jolly',
        usage='%(prog)s [options]',
        description='Download assignment from Canvas, run automated tests and email the results back to students.',
        epilog="examples: \n\
        # download list of courses/assignments\n\
        jolly --download\n\
        jolly css132 --download\n\
        # download all assignment submissions\n\
        jolly css132 ass1 --download\n\
        # download assignment submission from a specific user\n\
        jolly css132 ass1 pisan --download\n\
        # unzip all downloaded assignments\n\
        jolly css132 ass1 --unzip\n\
        # run all tests in given test directory that start with test_\n\
        jolly css132 ass1 --tdir sometestdir\n\
        # run tests from defaulttests that start with given prefix\n\
        jolly css132 ass1 --tdir sometestdir --tprefix test_cpplint,test_cppcheck\n\
        # email the jolly_toemail.txt files to all students\n\
        jolly css132 ass1 --email\n\
        # email with password authentication for email server\n\
        jolly css132 ass1 --email --pfile -\n\
        # download submission for one user, run all tests and email results\n\
        jolly css132 ass1 pisan --download --tdir sometestdir --email\n"
    )
    parser.add_argument("course_name",
                        nargs='?',
                        help='short course name, if course not found list all courses')
    parser.add_argument("assignment_name",
                        nargs='?',
                        help='short assignment name, if course given list all assignments')
    parser.add_argument("netids",
                        nargs='?',
                        help="netids of students separated by commans or leave empty for all students")
    parser.add_argument("--download", action='store_true',
                        help="download files from canvas")
    parser.add_argument("--createempty", action='store_true',
                        help="create empty directories even if there is no student assignment to download")
    parser.add_argument("--unzip", action='store_true',
                        help="unzip any zip files submitted")
    parser.add_argument(
        "--tdir",
        help="directory for test scripts, test files must be named test_xxx")
    parser.add_argument("--tprefix",
                        help="(advanced) run tests matching the given prefix separated by commas, default is 'test_'")
    parser.add_argument("--email", action='store_true',
                        help="email the contents of jolly_toemail.txt to each student")
    parser.add_argument("--esubject", help="customized email subject in quotes")
    parser.add_argument("--efile",
                        help="the file to send instead of jolly_toemail.txt")
    parser.add_argument("--eattach",
                        help="the file to attach in addition to sending jolly_toemail.txt")
    parser.add_argument("--pfile",
                        help="'-' for interactive, or the file with password to authenticate for SMTP/emails")

    args = parser.parse_args()
    if args.tdir and not args.tprefix:
        args.tprefix = "test_"
    elif args.tprefix and not args.tdir:
        args.tdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'defaulttests')
    jolly = Jolly(args.course_name, args.assignment_name, args.netids,
                  args.createempty, parser.format_help())
    if args.email:
        if args.efile:
            jolly.file_toemail = args.efile
        if args.eattach:
            jolly.file_toattach = args.eattach
    jolly.run(args.download, args.tdir, args.tprefix, args.unzip, args.email, args.esubject, args.pfile)


if __name__ == "__main__":
    main_entry()
