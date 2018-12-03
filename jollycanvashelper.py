#!/usr/bin/env python
"""
Download assignments from Canvas
"""

# To generate the limits and options, pylint --generate-rcfile
# pylint: disable=too-many-lines
# disable for only one line using it in-line # pylint: disable=line-too-long

import datetime
from datetime import timedelta
import json
import os
import re
import shutil
import tempfile
import urllib.parse
import urllib.request
from urllib.error import URLError, HTTPError
from collections import namedtuple

import jollyhelper

SINGLEPAGE = urllib.parse.urlencode({"per_page": "100", "page": "1"})

CUser = namedtuple('CUser', ['name', 'canvasid', 'netid'])


# indexed in Assignment.submissions by netid
# "pisan"
# Submission(filePack['id'], filePack['assignment_id'], filePack['user_id'], netid)

# pylint: disable-msg=too-few-public-methods
class Submission:
    def __init__(self, subid, assid, user_id, netid):
        self.subid = subid
        self.assid = assid
        self.user_id = user_id
        self.usernetid = netid
        self.attachments = []


# indexed in Course.assignments by name
# "Assignment 1"
class Assignment:
    def __init__(self, assid, name, url):
        self.assid = assid
        self.url = url
        self.name = name
        self.submissions = {}

    def addsubmission(self, submission):
        self.submissions[submission.usernetid] = submission


# indexed in Canvas.allcourses by sis_course_id
# "2017-autumn-CSS-142-B"
class Course:
    def __init__(self, canvas, course_id, name):
        self.course_id = course_id
        self.name = name
        self.assignments = {}
        # users indexed by id, that is canvasid
        self.users_by_canvas_id = {}
        self.netid2canvas_number = {}
        self.canvas_number2netid = {}
        self.canvas = canvas

    def get_user_by_netid(self, netid):
        if netid not in self.netid2canvas_number:
            return None
        return self.get_user_by_canvas_id(self.netid2canvas_number[netid])

    def get_user_by_canvas_id(self, canvasid):
        if canvasid not in self.users_by_canvas_id:
            return None
        return self.users_by_canvas_id[canvasid]

    def get_netids(self):
        netids = []
        for _loginid, user in self.users_by_canvas_id.items():
            netids.append(user.netid)

    # https://canvas.uw.edu/api/v1/courses/1175454/assignments?per_page=100&page=1
    def download_assignments(self):
        if self.assignments:
            return True
        print('Getting the list of assignments for %s' % self.name)
        url = "courses/" + str(self.course_id) + "/" + "assignments?" + SINGLEPAGE
        # print("URL is %s " % (url))
        assignments = self.canvas.get_url(url)
        if not assignments:
            print("Could not get assignments for %s" % self.name)
            return False
        # print(assignments)
        for ass in assignments:
            self.assignments[ass['name']] = Assignment(ass['id'], ass['name'], ass['submissions_download_url'])
            # print("Adding assignments: %s // %s %s" % (ass['id'], ass['name'], ass['submissions_download_url']))
        return True

    def find_download_assignment(self, assignmentname):
        self.download_assignments()
        if not self.assignments:
            return None
        for ass_name, ass in self.assignments.items():
            if ass_name == assignmentname:
                return ass
        return None

    def get_users(self):
        if self.users_by_canvas_id:
            return self.users_by_canvas_id
        print("Getting users for %s" % self.name)
        url = "courses/" + str(self.course_id) + "/" + "users?" + SINGLEPAGE
        # print("URL is %s " % (url))
        users = self.canvas.get_url(url)
        if not users:
            print("Could not get users for %s" % self)
            return None
        for user in users:
            canvasid = user['id']
            netid = user['login_id']
            self.users_by_canvas_id[canvasid] = CUser(user['name'], canvasid, netid)
            self.netid2canvas_number[netid] = canvasid
            self.canvas_number2netid[canvasid] = netid
            # print("Adding assignments: %s // %s %s" % (ass['id'], ass['name'], ass['submissions_download_url']))
        return self.users_by_canvas_id

    # https://canvas.uw.edu/api/v1/courses/1232772/assignments/4372076/submissions
    def get_submissions(self, ass):
        if ass.submissions:
            return
        print("Getting the list of submissions for %s" % ass.name)
        url = "courses/" + str(self.course_id) + "/" + "assignments/" + str(ass.assid) + "/submissions?" + SINGLEPAGE
        # print("URL is %s " % (url))
        submissions = self.canvas.get_url(url)
        if not submissions:
            print("Could not get submissions for %s" % ass)
            return
        for file_pack in submissions:
            if 'attachments' in file_pack:
                canvas_id = file_pack['user_id']
                user = self.get_user_by_canvas_id(canvas_id)
                netid = user.netid
                subm = Submission(file_pack['id'], file_pack['assignment_id'], canvas_id, netid)
                # print("Added submission: %s" % (subm))
                # print("Attach is %s" % (item['attachments']))
                for attachment in file_pack['attachments']:
                    fname = attachment['filename']
                    aurl = attachment['url']
                    # print("Adding %s at url %s " %(fname, aurl))
                    subm.attachments.append({'filename': fname, 'url': aurl})
                ass.addsubmission(subm)

    def list_users(self):
        print("netid => Name")
        print("=========================")
        sorted_d = sorted([(v.netid, v.name) for k, v in self.users_by_canvas_id.items()])
        for netid, name in sorted_d:
            print("%s => %s" % (netid, name))

    def list_assignments(self):
        print("Assignment Names")
        print("=========================")
        sorted_d = sorted([ass_name for ass_name, _ass in self.assignments.items()])
        for ass_name in sorted_d:
            print("%s" % ass_name)
        return sorted_d


class Canvas:
    AllCourses = {}

    def __init__(self):
        self.baseurl = jollyhelper.JH.get("canvasapi")
        self.logfilename = jollyhelper.JH.get("logfile")
        self.token = jollyhelper.JH.get("canvastoken")

    def get_course(self, coursename):
        return self.AllCourses[coursename]

    def get_assignment(self, coursename, assignmentname):
        if coursename in self.AllCourses:
            course = self.get_course(coursename)
            for name, ass in course.assignments.items():
                if assignmentname == name:
                    return ass
        return None

    @staticmethod
    def timestamp():
        dtnow = datetime.datetime.now()
        stamp = format("%04d%02d%02d%02d%02d%02d" %
                       (dtnow.year, dtnow.month, dtnow.day, dtnow.hour, dtnow.minute, dtnow.second))
        return stamp

    def get_url(self, url):
        if not self.token:
            return None
        url_string = self.baseurl + url
        # print("Requesting: %s" % urlString)
        request = urllib.request.Request(url_string)
        request.add_header("Authorization", "Bearer " + self.token)
        try:
            response = urllib.request.urlopen(request)
            jstr = response.read().decode('utf-8')
            return json.loads(jstr)
        except HTTPError as err:
            # SSL CERTIFICATE_VERIFY_FAILED on Mac fixed by /Applications/Python\ 3.6/Install\ Certificates.command
            # https://stackoverflow.com/questions/40684543/how-to-make-python-use-ca-certificates-from-mac-os-truststore
            print("HTML error for %s: %s %s" % (url_string, err.reason, err.reason))
            return None
        except URLError as err:
            print("HTML error for %s: %s %s" % (url_string, err.reason, err.reason))
            return None

    # "2017-12-10T08:00:00Z
    @staticmethod
    def course_is_current(startdate, enddate):
        now = datetime.date.today()
        # if more than a year it was created
        if startdate is not None:
            starting_at = datetime.date(int(startdate[0:4]), int(startdate[5:7]), int(startdate[8:10]))
            if (starting_at + timedelta(days=365)) < now:
                return False
        if enddate is not None:
            ending_at = datetime.date(int(enddate[0:4]), int(enddate[5:7]), int(enddate[8:10]))
            if now > ending_at:
                return False
        return True

    # https://canvas.uw.edu/api/v1/courses?per_page=100&page=1
    def get_courses(self):
        if self.AllCourses:
            return True
        # print("Getting the list of courses from Canvas")
        courses = self.get_url("courses?" + SINGLEPAGE)
        if not courses:
            print("Could not get the list of courses")
            return False
        for course in courses:
            if 'end_at' in course:
                # started_at is null for future courses
                start_date = course['created_at']
                end_date = course['end_at']
                # if 'sis_course_id' in course:
                #     print("At: %s" %course['sis_course_id'])
                #     print("%s %s %s" %(startDate, endDate, self.course_is_current(startDate, endDate)))
                if 'sis_course_id' in course and \
                        course['sis_course_id'] and \
                        Canvas.course_is_current(start_date, end_date):
                    # print("Adding courses: %s // %s // %s" % (course['id'], course['sis_course_id'], course['name']))
                    # print("Got %s for %s" %(self.courseHasNotEnded(endDate), endDate))
                    self.AllCourses[course['sis_course_id']] = Course(self, course['id'], course['name'])
                    # print("Skipping course without sis_course_id: %s" % (course['name']))
        return True

    def list_courses(self):
        print("Course Name => Long Course Name")
        print("=========================")
        sorted_d = sorted([(course_id, course.name) for course_id, course in self.AllCourses.items()])
        for course_id, name in sorted_d:
            print("%s => %s" % (course_id, name))
        return sorted_d

    def download(self, course: Course, assignment: Assignment, users, createempty):
        if not course or not assignment or not users:
            print("Unexpected arguments to Canvas.download %s %s %s" % (course, assignment, users))
            return False
        return self.get_files(course, assignment, users, createempty)

    @staticmethod
    def mkdir_if_needed(target):
        try:
            if not os.path.isdir(target):
                os.mkdir(target)
            return True
        except OSError as err:
            print("ERR: Failed to make directory %s, check permissions: %s" % (target, err.strerror))
            return False

    @staticmethod
    def writefileinfo(filename):
        if not os.path.isfile(filename):
            with open(filename, "w") as outfile:
                outfile.write("")
        if not os.path.isfile(filename):
            print("ERR: Failed to create file %s" % filename)
            return False
        return True

    @staticmethod
    def writeuserdetails(targetdir, netid, name):
        Canvas.writefileinfo(os.path.join(targetdir, format("jolly_netid_%s.txt" % netid)))
        sanename = jollyhelper.sanitize_string(name)
        Canvas.writefileinfo(os.path.join(targetdir, format("jolly_name_%s.txt" % sanename)))

    @staticmethod
    def get_files_user(submissions, user, userdir, logfile):
        if user.netid not in submissions:
            return False
        if not Canvas.mkdir_if_needed(userdir):
            return False
        for attachment in submissions[user.netid].attachments:
            # print("\tAttachment: %s" % (attachment))
            fnamefinal = os.path.join(userdir, attachment['filename'])
            if os.path.isfile(fnamefinal):
                print("For (%s) %s, already downloaded %s" % (
                    user.netid, user.name, attachment['filename']))
                continue
            print("For (%s) %s, downloading %s" % (user.netid, user.name, attachment['filename']))
            with urllib.request.urlopen(attachment['url']) as response:
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    shutil.copyfileobj(response, tmp)
            # print(time.ctime())
            shutil.move(tmp.name, fnamefinal)
            if not os.path.isfile(fnamefinal):
                print("ERR: Failed to create %s" % fnamefinal)
            Canvas.writefileinfo(os.path.join(userdir, "jolly_downloaded.txt"))
            with open(logfile, "a") as logfileout:
                logfileout.write("Downloaded %s\n" % attachment['filename'])
        return True

    def get_files(self, course: Course, assignment: Assignment, users: dict, createempty: bool):
        targetdir = "."
        targetdir = os.path.abspath(os.path.join(targetdir, jollyhelper.sanitize_string(assignment.name)))
        if not Canvas.mkdir_if_needed(targetdir):
            return False
        print("Created assignment directory %s" % targetdir)
        # print("Downloading assignment submissions: %s" % (assignment.name))
        # print("Submissions are: %s" % (assignment.submissions))
        downloadedsomething = {}
        for _canvasid, user in users.items():
            downloadedsomething[user.netid] = False
            userdir = os.path.join(targetdir, user.netid)
            logfile = os.path.join(userdir, self.logfilename)
            downloadedsomething[user.netid] = self.get_files_user(assignment.submissions, user, userdir, logfile)
            if downloadedsomething[user.netid]:
                self.writeuserdetails(userdir, user.netid, user.name)
            elif createempty:
                if not Canvas.mkdir_if_needed(userdir):
                    continue
                self.writeuserdetails(userdir, user.netid, user.name)
                with open(logfile, "w") as logfileout:
                    logfileout.write("")
        for netid, _value in downloadedsomething.items():
            if not downloadedsomething[netid]:
                user = course.users_by_canvas_id[course.netid2canvas_number[netid]]
                print("No files to download for (%s) %s" % (netid, user.name))
        return True


if __name__ == "__main__":
    print("Import jollycanvashelper file from jolly")
