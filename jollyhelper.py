#!/usr/bin/env python3
"""Helper files for JollyFeedBack """

import configparser
import getpass
import os
import pwd
import re
import shutil
import smtplib
import socket
import subprocess
import sys
import tempfile
import time
import zipfile
from email.encoders import encode_base64
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

if not sys.version_info >= (3, 5):
    print("%s needs python 3.5 or later" % __file__)
    sys.exit(-1)

USER_INI = 'jollyconfig.ini'
DEFAULT_INI = os.path.join(os.path.dirname(__file__), 'jollyconfig-defaults.ini')


class JollyHelperGlobals:
    """Globals through singleton"""
    globals = {}

    @staticmethod
    def get(mkey):
        if mkey in JH.globals:
            return JH.globals[mkey]
        return None

    @staticmethod
    def read_configs():
        try:
            config = configparser.ConfigParser(allow_no_value=True)
            config.read(DEFAULT_INI)
            for key, value in config['DEFAULT'].items():
                JH.globals[key] = value
            default_ini = 'jolly'
            possibilities = ['~' + os.sep + '.' + default_ini, '~' + os.sep + default_ini + '.ini',
                             '.' + default_ini, default_ini + '.ini']
            fnames = []
            found = False
            fname = ""
            for configfile in possibilities:
                fname = os.path.abspath(os.path.expanduser(configfile))
                fnames.append(fname)
                if os.path.isfile(fname):
                    found = True
                    break
            if not found:
                print("ERR: Could not find configuration file for the CANVASTOKEN")
                for file in fnames:
                    print("Looked at %s " % file)
                print(JH.get("canvas_token_help"))
                return False
            config2 = configparser.ConfigParser()
            config2.read(fname)
            for key, value in config2['DEFAULT'].items():
                JH.globals[key] = value
            if not JH.get("canvastoken") or JH.get("canvastoken") == '':
                print("ERR: Could not find CANVASTOKEN in %s" % fname)
                print(JH.get("canvas_token_help"))
                return False
        except configparser.Error as err:
            print("ERR: Could not parse the configuration file: %s" % err)
            return False
        return True


# try:
#     JH
# except NameError:
#     # defining it now
#     JH = JollyHelperGlobals()
#     JH.read_configs()

JH = JollyHelperGlobals()
if not JH.read_configs():
    sys.exit(10)

JH.globals["testerpath"] = os.path.dirname(os.path.realpath(__file__))


def insert_file_at_end(in_fle, textfile, outfile):
    if not os.path.isfile(in_fle):
        print("SCRIPT ERROR: %s is not found" % in_fle)
        return None
    if not os.path.isfile(textfile):
        print("SCRIPT ERROR: %s is not found" % textfile)
        return None
    with open(textfile) as file:
        lines = file.readlines()
    lines = "".join(lines)
    with open(in_fle) as file:
        flines = file.readlines()
    flines = "".join(flines)
    with open(outfile, "w") as out:
        out.write(flines)
        out.write(lines)
    return None


############################################
# Unzip files
############################################

# replace all non letters and numbers with underscore
def sanitize_string(string):
    return re.sub(r'[^0-9a-zA-Z_-]+', '_', string)


def unzip_files_for_assignment(ass_name, netids):
    assfull = os.path.abspath(sanitize_string(ass_name))
    if not os.path.isdir(assfull):
        print("TESTERR: Could not find directory %s for downloaded files" % assfull)
        return
    for netid in netids:
        userdir = os.path.join(assfull, netid)
        if os.path.isdir(userdir):
            unzip_files_in_directory(userdir)


def unzip_files_in_directory(indir='.'):
    pat = "^.*zip$"
    prog = re.compile(pat)
    zips = [f for f in os.listdir(indir)
            if prog.match(f) and os.path.isfile(os.path.join(indir, f))]
    targetdir = indir
    for zipf in zips:
        zipfull = os.path.join(indir, zipf)
        if not zipfull or not os.path.isfile(zipfull) or not zipfile.is_zipfile(zipfull):
            print("SCRIPT ERROR: zipfile %s is not found" % zipfull)
        else:
            unzip_file(zipfull, targetdir)


def unzip_file(zipf: str, targetdir: str):
    zipbase = os.path.basename(zipf)
    (zipdir, _) = os.path.splitext(zipbase)
    zipfilesdir = os.path.join(targetdir, zipdir)
    if os.path.isdir(zipfilesdir):
        print("--> Skipping %s, subdirectory exists" % zipbase)
        return targetdir
    print("--> Unzipping %s to %s" % (zipf, targetdir))
    with zipfile.ZipFile(zipf, "r") as zipref:
        zipref.extractall(path=targetdir)
    if not os.path.isdir(zipfilesdir):
        print("*** Unzipped %s, but could not find directory %s for the files"
              % (zipf, zipfilesdir))
        # if a directory exists, rename it
        if os.path.isfile(zipfilesdir):
            os.rename(zipfilesdir, zipfilesdir + "-tester-renamed")
        # create new directory
        os.mkdir(zipfilesdir)
        print("*** Creating new directory %s to extract the zip file" % zipfilesdir)
        # extract to correct directory
        with zipfile.ZipFile(zipf, "r") as zipref:
            zipref.extractall(path=zipfilesdir)
        if os.path.isdir(zipfilesdir):
            return targetdir
        return None
    return targetdir


def start_help_separator(msg, out=sys.stdout):
    print("* Start: " + msg, file=out)
    print("==================================================", file=out, flush=True)


def end_help_separator(msg, out=sys.stdout):
    print("\n" + "* End: " + msg, file=out)
    print("==================================================", file=out, flush=True)


def list_files():
    """List the files, except for tester_ files created by Jolly"""
    helpermsg = format("listing files in directory")
    start_help_separator(helpermsg)
    files = os.listdir('.')
    pat = "^jolly_.*$"
    prog = re.compile(pat)
    files = [f for f in files if os.path.isfile(f) and f[0] != '.' and (not prog.match(f))]
    print(files)
    end_help_separator(helpermsg)


def get_netids_from_directory(mydir):
    pat = "^[a-z]+[a-z0-9]+$"
    prog = re.compile(pat)
    files = [f for f in os.listdir(mydir) if prog.match(f)]
    return files


def dir_list(pat):
    files = os.listdir('.')
    prog = re.compile(pat)
    files = [f for f in files if os.path.isfile(f) and prog.match(f)]
    return files


def dir_list_dirs(pat):
    files = os.listdir('.')
    prog = re.compile(pat)
    files = [f for f in files if os.path.isdir(f) and prog.match(f)]
    return files


def generic_file_components(file, srcext, exeext):
    srcmatch = re.compile("^(.*)" + srcext + "$").match(file)
    exematch = re.compile("^(.*)" + exeext + "$").match(file)
    if srcmatch:
        basefile = srcmatch.group(1)
        srcfile = basefile + srcext
        exefile = basefile + exeext
    elif exematch:
        basefile = exematch.group(1)
        srcfile = basefile + srcext
        exefile = basefile + exeext
    else:
        # assuming bare file
        basefile = file
        srcfile = basefile + srcext
        exefile = basefile + exeext
    return basefile, srcfile, exefile


def javafile2components(file):
    return generic_file_components(file, ".java", ".class")


def cfile2components(file):
    return generic_file_components(file, ".c", ".exe")


def cppfile2components(file):
    return generic_file_components(file, ".cpp", ".exe")


def generic_compile(compiler, cflags, srcfiles, exefile):
    helpermsg = format("compiling %s" % srcfiles)
    start_help_separator(helpermsg)
    # assume all srcfiles exist
    if os.path.isfile(exefile):
        os.remove(exefile)
    command = [compiler] + cflags + srcfiles
    result = subprocess.run(command)
    if result.returncode != 0 or not os.path.isfile(exefile):
        print("ALERT: Failed to compile %s using %s"
              % (srcfiles, " ".join(command)), flush=True)
    if result.returncode == 0 and os.path.isfile(exefile):
        print("Compiled %s and got %s" % (srcfiles, exefile))
    end_help_separator(helpermsg)


def cpp_compile(givenfiles, cppexe):
    if not isinstance(givenfiles, list) or givenfiles == []:
        print("ALERT: Need a list of cpp files to compile: %s" % givenfiles)
        return
    generic_compile(JH.get("cppcompiler"), JH.get("cppflags").split(',') + [cppexe], givenfiles, cppexe)


def generic_run_short(vmrunner, vmflags, suppress=False, pattern=None):
    helper_msg = format("running %s" % vmrunner)
    start_help_separator(helper_msg)
    command = [vmrunner] + vmflags
    result = generic_runc(command, suppress, pattern)
    if not suppress and (not result or result.returncode):
        print("*** ALERT: Got an error when running %s using %s" % (vmrunner, command), flush=True)
        return -1
    end_help_separator(helper_msg)
    if not result:
        return None
    return result.returncode


def read_print_nlines(fname, number, pattern=None):
    cnt = 1
    prog = ""
    if pattern is not None:
        prog = re.compile(pattern)
    with open(fname) as fpx:
        line = fpx.readline()
        while line and cnt < number:
            if not pattern or prog.search(line):
                print(line, end='')
            line = fpx.readline()
            cnt += 1
    return cnt


# Modified to write to a temporary file
# and then only read 1000 lines from that file
def generic_runc(command, suppress=False, pattern=None):
    ftmp = tempfile.NamedTemporaryFile(delete=False)
    max_lines = 1000
    commandstr = " ".join(command)
    result = None
    try:
        # print("XXX command is %s" % command)
        with open(ftmp.name, "w") as ftmpout:
            timeout = int(JH.get("timeout"))
            result = subprocess.run(command, stderr=ftmpout, stdout=ftmpout, timeout=timeout)
            # done with the file read 1000 lines and spit it out
            if read_print_nlines(ftmp.name, max_lines, pattern) >= max_lines:
                print("\nALERT: Output truncated from %s at %s lines" % (commandstr, max_lines))
            if os.path.isfile(ftmp.name):
                os.unlink(ftmp.name)
    except subprocess.TimeoutExpired as err:
        if read_print_nlines(ftmp.name, max_lines, pattern) >= max_lines:
            print("\nALERT: Output truncated from %s at %s lines" % (commandstr, max_lines))
        print("ALERT: Ran out of time when running %s " % commandstr)
        print("ALERT: Possible cause waiting for keyboard input")
        print("ALERT: Possible cause infinite loop")
        print("TimeoutExpired error: {0}".format(err))
        if os.path.isfile(ftmp.name):
            os.unlink(ftmp.name)
    if not suppress and (not result or result.returncode):
        print("ALERT: Got an error when running %s" % commandstr, flush=True)
    if os.path.isfile(ftmp.name):
        os.unlink(ftmp.name)
    return result


def generic_run(vmrunner, vmflags, exefile):
    helper_msg = format("running %s" % exefile)
    start_help_separator(helper_msg)
    command = [exefile] if not vmrunner else [vmrunner] + vmflags + [exefile]
    result = generic_runc(command)
    if not result or result.returncode:
        print("ALERT: Got an error when running %s using %s" % (exefile, command), flush=True)
        return -1
    end_help_separator(helper_msg)
    if not result:
        return None
    return result.returncode


def java_run(givenfile=None):
    if not givenfile or (isinstance(givenfile, list) and givenfile == []):
        files = dir_list(".*.class$")
    elif isinstance(givenfile, list):
        files = givenfile
    else:
        files = [givenfile]
    for file in files:
        (java_base, _, _) = javafile2components(file)
        generic_run(JH.get("javavm"), JH.get("javaflags").split, java_base)


def c_run(givenfile=None):
    if not givenfile or (isinstance(givenfile, list) and givenfile == []):
        files = dir_list(".*.exe$")
    elif isinstance(givenfile, list):
        files = givenfile
    else:
        files = [givenfile]
    for file in files:
        (_, _, c_exe) = cfile2components(file)
        if os.path.isfile(c_exe):
            generic_run(None, [], "./" + c_exe)
        else:
            print("ALERT: Could not find %s to run" % c_exe)


# valgrind has a bug where it can get signal 11
# and will continue to write that line for 100+MB file
# need to dump contents of the file to a text,
# read only certain number of lines and
def valgrind_run(cexe):
    helper_msg = format("valgrind on %s" % cexe)
    start_help_separator(helper_msg)
    pattern = "definitely lost:"
    generic_run_short(JH.get("valgrind"), [cexe], False, pattern)
    helper_msg = format("finished valgrind on %s" % cexe)
    end_help_separator(helper_msg)


def cpp_compile_run(givenfiles):
    if not isinstance(givenfiles, list) or givenfiles == []:
        print("ALERT: Need a list of cpp files to compile and run: %s" % givenfiles)
        return
    (_, _, cpp_exe) = cppfile2components(givenfiles[0])
    cpp_compile(givenfiles, cpp_exe)
    c_run(cpp_exe)


def c_clean_exe_files():
    files = dir_list(".*.exe$")
    for file in files:
        os.unlink(file)
    dirs = dir_list_dirs(".*.exe.dSYM$")
    for dirx in dirs:
        shutil.rmtree(dirx)


###########################################################################
# Mail Section
###########################################################################
def get_name_from_tester_file():
    files = os.listdir('.')
    pat = "^jolly_name_([^_]+)_(.+).txt$"
    prog = re.compile(pat)
    for file in files:
        result = prog.match(file)
        if result:
            last_name = result.group(1)
            first_name = result.group(2)
            # firstName can be John_Mary, so must open it up
            first_name = first_name.replace("_", " ")
            last_name = last_name.replace("_", " ")
            return last_name, first_name
    return None, None


def get_netid_from_tester_file():
    files = os.listdir('.')
    pat = "^jolly_netid_(.*).txt$"
    prog = re.compile(pat)
    student_email = None
    for file in files:
        result = prog.match(file)
        if result:
            student_email = format("%s@%s" % (result.group(1), JH.get("emaildomain")))
    # student_email = format("nobody@%s" % JH.get("emaildomain"))
    return student_email


def mail_write_introduction(fpx, introfile=None, name=None):
    msg1 = "Hi," if not name else "Hi " + name + ","
    msg2 = JH.get("intromessage")
    msg = "\n" + msg1 + "\n" + msg2
    if (introfile is not None) and os.path.isfile(introfile):
        with open(introfile) as introfp:
            msg = msg + "".join(introfp.readlines())
    fpx.write(msg)


def mail_send_via_smtp(fromemail, recipents, msg, user=None, password=None):
    try:
        smtpserver = JH.get("smtpserver")
        smtp_connection = smtplib.SMTP(smtpserver, 587)
        smtp_connection.starttls()
        if user is not None and password is not None:
            smtp_connection.login(user, password)
        smtp_connection.sendmail(fromemail, recipents, msg)
        smtp_connection.quit()
        return True
    except smtplib.SMTPException as err:
        print("*** Could not send email")
        print("*** SMTP error message was %s" % err)
        return False


def hostname_is_valid(hostname):
    try:
        socket.gethostbyname(hostname)
        return True
    except socket.error:
        return False


def email_is_valid(emailaddress):
    if not emailaddress:
        return False
    # pylint: disable=anomalous-backslash-in-string
    email_regex = "\A[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
    email_regex = email_regex + "@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+"
    email_regex = email_regex + "[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
    return re.compile(email_regex).match(emailaddress)


def get_full_from_name(fromemail):
    fromname = pwd.getpwuid(os.getuid())[4]
    return format("\"%s\" <%s>" % (fromname, fromemail))


def get_full_to_name(toemail):
    (firstname, lastname) = get_name_from_tester_file()
    if not lastname or not firstname:
        return format("<%s>" % toemail)
    return format("\"%s %s\" <%s>" % (firstname, lastname, toemail))


def mail_attach_file(filetoattach):
    # if we also have an attachment
    if filetoattach:
        if os.path.isfile(filetoattach):
            with open(filetoattach, "rb") as opened:
                openedfile = opened.read()
                attachedfile = MIMEApplication(openedfile, _subtype="pdf",
                                               _encoder=encode_base64)
                attachedfile.add_header('content-disposition', 'attachment', filename=filetoattach)
        else:
            print("Email attachment %s is not found" % filetoattach)
            return None
    return attachedfile


# pylint: disable-msg=too-many-branches
# pylint: disable-msg=too-many-statements
# pylint: disable-msg=too-many-locals
# pylint: disable-msg=too-many-return-statements
def mail_send_file(subject=None, password=None, reallysend=False,
                   filetosend=None, filetoattach=None):
    filetosaveemail = JH.get("emailfilesave")
    toemail = get_netid_from_tester_file()
    if os.path.isfile(filetosaveemail):
        print("Skipping, already sent email to %s" % toemail)
        return
    # check fromEmail
    loginid = getpass.getuser()
    networkid = re.compile(r'.+\\(.+)$').match(loginid)
    if networkid:
        loginid = networkid.group(1)
    from_email = format("%s@%s" % (loginid, JH.get("emaildomain")))
    if not email_is_valid(from_email) or not toemail or not email_is_valid(toemail):
        print("SCRIPT ERROR: Check email addresses from:%s to:%s" % (from_email, toemail))
        return
    # check filetosend
    filetosend = os.path.abspath(os.path.expanduser(filetosend))
    if not os.path.isfile(filetosend):
        print("SCRIPT ERROR: The filetosend %s could not be found. Did you run any tests?" % filetosend)
        return
    # check smtpserver
    if not hostname_is_valid(JH.get("smtpserver")):
        print("SCRIPT ERROR: The smtpserver %s could not be resolved" % JH.get("smtpserver"))
        return
    # Enough checks, lets do it
    (to_firstname, _to_lastname) = get_name_from_tester_file()
    full_to_name = get_full_to_name(toemail)
    full_from_name = get_full_from_name(from_email)
    # Read filetosend
    # Check if filke is too big in bytes 1MB = 1000000 bytes
    # max 0.5MB = 500000
    if os.path.getsize(filetosend) < 500000:
        with open(filetosend) as testerlog:
            tester_lines = testerlog.read()
    else:
        # read only 1000 lines
        with open(filetosend) as testerlog:
            head = [next(testerlog) for _x in range(1000)]
        tester_lines = head + ["\n\n The log file is too large. It has been truncated! \n"]
    # Prepare saved version of email
    fileforintrotext = JH.get("intromessage")
    with open(filetosaveemail, "w") as fpx:
        fpx.write(format("From: %s\nTo: %s\nSubject: %s\n\n" % (full_from_name, full_to_name, subject)))
        mail_write_introduction(fpx, fileforintrotext, to_firstname)
        start_help_separator(format("\n\nSent from %s to %s on %s\n" %
                                    (full_from_name, full_to_name, time.strftime("%Y-%m-%d %H:%M:%S"))), fpx)
        fpx.write(tester_lines)
    # Email files saved, open and read it
    with open(filetosaveemail) as fpx:
        _discard_from = fpx.readline()
        _discard_to = fpx.readline()
        _discard_subject = fpx.readline()
        msgbody = fpx.read()
    # msg = email.mime.text.MIMEText(msgbody)
    msg = MIMEMultipart('alternative')
    msg['From'] = full_from_name
    msg['To'] = full_to_name
    msg['Subject'] = subject
    part1 = MIMEText(msgbody, 'plain')
    htmlpart = "<div><pre>\n" + msgbody + "\n</pre></div>\n"
    part2 = MIMEText(htmlpart, 'html')
    msg.attach(part1)
    msg.attach(part2)
    # if we also have an attachment
    attachedfile = mail_attach_file(filetoattach)
    if attachedfile:
        msg.attach(attachedfile)
    recipients = [from_email, toemail]
    # CHECK if you REALLY want to send it
    if reallysend:
        timedelay = int(JH.get("mailtimedelay"))
        helpermsg = format("Sending mail to %s" % full_to_name)
        print(helpermsg)
        if mail_send_via_smtp(from_email, recipients, msg.as_string(),
                              user=loginid, password=password):
            print('.... delay of %s seconds not to overwhelm the mail server....' % timedelay)
            time.sleep(timedelay)
        else:
            print("ERR: Could not send email!")
            print("ERR: Did you use --pfile with '-' for interactive or with file name")
    else:
        helpermsg = format("--reallysend is FALSE so not actually sending mail to %s" % full_to_name)
        print(helpermsg)


if __name__ == "__main__":
    print("This is jollyhelper, import it from Jolly")
