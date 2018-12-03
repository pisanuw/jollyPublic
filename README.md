# Jolly Feedback

Set of scripts to download student assignments from Canvas, run customized tests on them 
and email the results back to students.

## Getting Started

Download the project from https://github.com/pisanuw/jolly

### Prerequisites

python3

### Installing


Unzip the project in a directory, such as `~/jolly/`


```
~/jolly/jolly.py
```

You will get a message about getting a special Canvas token, which is necessary for Jolly 
to connect to canvas. 

To generate the token:

1. Login to Canvas using your web browser
2. Go to Account > Settings
3. Under "Approved Integrations" click on "New Access Token", generate the token and copy it

To get Jolly to use the token:

1. Create a file called `.jolly` (or `jolly.ini`) in your home directory.
2. The contents of the file should be as follows:
```
[DEFAULT]
CANVASTOKEN = 10~xxxxxxxxx
```
3. This file should only be readable by you (`chmod 600 .jolly` would do the trick)


Run `~/jolly/jolly.py` and you should get usage and example information:

```
usage: jolly [options]

Download assignment from Canvas, run automated tests and email the results back to students.

positional arguments:
  course_name          short course name, if course not found list all courses
  assignment_name      short assignment name, if course given list all assignments
  netids               netids of students separated by commans or leave empty for all students

optional arguments:
  -h, --help           show this help message and exit
  --download           download files from canvas
  --createempty        create empty directories even if there is no student assignment to download
  --unzip              unzip any zip files submitted
  --tdir TDIR          directory for test scripts, test files must be named test_xxx
  --tprefix TPREFIX    (advanced) run tests matching the given prefix separated by commas, default is 'test_'
  --email              email the contents of jolly_toemail.txt to each student
  --esubject ESUBJECT  customized email subject in quotes
  --pfile PFILE        '-' for interactive, or the file with password to authenticate for SMTP/emails

examples: 
        # download list of courses/assignments
        jolly --download
        jolly css132 --download
        # download all assignment submissions
        jolly css132 ass1 --download
        # download assignment submission from a specific user
        jolly css132 ass1 pisan --download
        # unzip all downloaded assignments
        jolly css132 ass1 --unzip
        # run all tests in given test directory that start with test_
        jolly css132 ass1 --tdir sometestdir
        # run tests from defaulttests that start with given prefix
        jolly css132 ass1 --tdir sometestdir --tprefix test_cpplint,test_cppcheck
        # email the jolly_toemail.txt files to all students
        jolly css132 ass1 --email
        # email with password authentication for email server
        jolly css132 ass1 --email --pfile -
        # download submission for one user, run all tests and email results
        jolly css132 ass1 pisan --download --tdir sometestdir --email

ERR: Specify --download to get a list of courses
```

You are now ready to stary using Jolly

```buildoutcfg
$ ~/jolly/jolly.py --download

Course Name => Long Course Name
=========================
2018-autumn-CSS-132-A => CSS 132 A Au 18: Computer Programming For Engineers I
2018-autumn-CSS-343-A => CSS 343 A Au 18: Data Structures, Algorithms, And Discrete Mathematics II
2018-autumn-CSS-390-C => CSS 390 C Au 18: Special Topics
2018-autumn-CSS-422-B => CSS 422 B Au 18: Hardware And Computer Organization
2018-autumn-CSSSKL-132-A => CSSSKL 132 A Au 18: Computer Programming For Engineers Skills I
2019-winter-CSS-133-A => CSS 133 A Wi 19: Computer Programming For Engineers II
2019-winter-CSS-343-B => CSS 343 B Wi 19: Data Structures, Algorithms, And Discrete Mathematics II

Specify a course name
try: jolly COURSENAME --download

$ ~/jolly/jolly.py 2018-autumn-CSS-132-A --download

Getting the list of assignments for CSS 132 A Au 18: Computer Programming For Engineers I
Assignment Names
=========================
Quiz: 1 Introduction to Computers and C++
Quiz: 2 Input/Output and Operators
Quiz: 3 Introduction to Classes, Objects, Member Functions and Strings
Ass-1
Ass-2
Ass-3

Specify an assignment
try: jolly 2018-autumn-CSS-132-A ASSIGNMENT --download

$ ~/jolly/jolly.py 2018-autumn-CSS-132-A Ass-1 --download

Getting the list of assignments for CSS 132 A Au 18: Computer Programming For Engineers I
Getting users for CSS 132 A Au 18: Computer Programming For Engineers I
Getting the list of submissions for Ass-1
Created assignment directory /Users/pisan/tmp/Ass-1
For (johndoe) John Doe, downloading main.cpp
...
downloading all submissions to "Ass-1" directory
...

$ ~/jolly/jolly.py 2018-autumn-CSS-132-A Ass-1 johndoe --
Getting the list of assignments for CSS 132 A Au 18: Computer Programming For Engineers I
Getting users for CSS 132 A Au 18: Computer Programming For Engineers I
Getting the list of submissions for Ass-1
Created assignment directory /Users/pisan/tmp/Ass-1
For (johndoe) John Doe, already downloaded main.cpp

$ ~/jolly/jolly.py 2018-autumn-CSS-132-A Ass-1 johndoe --tprefix test_cpplint
Test files found are:  ['test_cpplint.py']
Looking at johndoe
	[Success] /code/jolly/defaulttests/test_cpplint.py
```

## Tests

There are several default tests provided in `defaulttests` directory to get you started.

You can use `--tdir somedirectory` to point Jolly to tests you have written. 
It will execute all files that match have a name matching `test_`

To run a single test or a small group fo tests, use `--tdir somedirectory --tprefix specialtests_`. 
All files in the given directory that have a name starting with `specialtests_`` will be run.
 
A test file can be written in any language. It will be called with the current directory 
as the student assignment directory, such as `Ass-1/johndoe/` in the above example.

Several special files are also created in each of the student directories:

`jolly_netid_johndoe.txt` - the netid of the student
\
`jolly_name_John_Doe.txt` - firstname and lastname of the student
\
`jolly_downloaded.txt` - empty file to indicate files have been downloaded.
If you want to download the files again, you need to remove this file.
\
`jolly_log.txt` - the output from tests from the last run of jolly
\
`jolly_toemail.txt` - the default file that will be emailed to student if `--email` option is used. 
\
`jolly_emailedfile.txt` - a copy of the email that was sent out via `--email`.
A copy of the email is also sent to the user running the Jolly script using carbon copy, `CC:`. 
If you want to send a second email to students, you will need to remove this file

## Sample Tests

Here is a sample testing file `test_cpplint.py`. This test will be executed either when all tests are executed or
when Jolly si called with `--tprefix test_cpplint` 

```python
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
         "--filter=-legal/copyright,-whitespace/tab,-build/namespaces"""
         ]

# exit code will not be zero if any errors found, so don't print an error message for that
jolly.Jolly.run_test("cpplint", flags, allimps, True)
```

Some tests, such as `--unzip`, `--email` are built into jolly.

When sending emails, `--esubject` can be used to set the subject line or the subject line can be set from
configuration options (see below). The email is sent to `netid@EMAILDOMAIN`. The `netid` is determined
by looking at the file name `jolly_netid_johndoe.txt` and the domain is set in configuration options.
A copy of all emails are also sent to the user running the jolly script, as well as being placed in the
`jolly_emailedfile.txt` file.

## Configuration Options

You can specify additional defaults in the `./jolly` (or `jolly.ini`) configuration file

```properties

[DEFAULT]

# Canvas token is required to access Canvas without using a password
CANVASTOKEN = 10~xxxxxxxxx

# Maximum time allowed for any test
TIMEOUT = 5

# Delay between sending emails, too many quick emails will get us marked as spammer
MAILTIMEDELAY = 15

JAVACOMPILER = javac

JAVAVM = java

JAVAFLAGS = -ea

CCOMPILER = gcc

CPPCOMPILER = g++

VALGRIND = valgrind

CPPFLAGS = -std=c++14,-Wall,-Wextra,-Wno-sign-compare,-g,-o

CFLAGS = -Wall,-Wextra,-g,-o'

# Emails are assumed to be netid@EMAILDOMAIN
EMAILDOMAIN = uw.edu

# Default subject line for emails
EMAILSUBJECT = Automated feedback from JollyFeedback Script

# Server for sending emails
SMTPSERVER = smtp.uw.edu

# The URL to talk to Canvas API
CANVASAPI = https://canvas.uw.edu/api/v1/

```

## Sending Emails

Some (most?) email servers require the user to authenticate before allowing them to send an email message.
If an authentication is required, use `--pfile -` to get Jolly to ask the password or use `--pfile secrretfile`
where the `secretfile` has the password on the first line.

`smtp.uw.edu` does not require a password if connected from on-campus or using VPN (such as Husky OnNet)to connect.

## Authors

* **Yusuf Pisan** - *Initial work* - https://github.com/pisanuw


## Acknowledgments

* Automated feedback systems have a long history, but the 2002 [Submit!](https://scholar.google.com/citations?user=eCpI_aUAAAAJ&hl=en&oi=ao) paper is where it all started for me.


