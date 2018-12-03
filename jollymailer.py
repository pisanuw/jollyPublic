#!/usr/bin/env python3
"""
Call the function from jollyhelper directly through a script
This is useful, so we can use the subprocess mechanism and easily
timeout or kill the script
"""

import argparse

import jollyhelper

# def mailSendFile(toEmail, subject, textfile, fromname="",
#                 authfile='~/private/jollyauth.txt',
#                 smtpServer='smtp.uw.edu',
#                 filetosaveemail="tester_emailedfile.txt", timedelay=15, reallysend=False):

#
# example:
# ./jollymailer.py --fromemail pisan@uw.edu --toemail pisan@uw.edu
# --subject "Test3" --filetosend "test.txt" --reallysend
#
if __name__ == "__main__":
    # pylint: disable=line-too-long
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("--fromemail",
                        help='from address in the form of xxx@yyy.edu', required=True)
    PARSER.add_argument("--toemail",
                        help="specify or get from file testern_netid_xxx")
    PARSER.add_argument("--subject", default='Comments from JollyFeedback Automated Script',
                        help='subject: line (default: %(default)s)')
    PARSER.add_argument("--filetosend", default='tester_logfile.txt',
                        help='what file to send (default: %(default)s)')
    PARSER.add_argument("--filetoattach", default='',
                        help='what file to attach (default: %(default)s)')
    PARSER.add_argument("--fromname", default=None,
                        help='actual name such as "cris doe"')
    PARSER.add_argument("--smtpauthfile", default="~/private/jollyauth.txt",
                        help='username/pass to login to smtp server (default: %(default)s)')
    PARSER.add_argument("--smtpserver", default='smtp.uw.edu',
                        help='smtp server to use (default: %(default)s)')
    PARSER.add_argument("--filetosaveemail", default='tester_emailedfiled.txt',
                        help='save a copy of the email sent in (default: %(default)s)')
    PARSER.add_argument("--timedelay", default=15, type=int,
                        help='seconds to wait between emails (default: %(default)s)')
    PARSER.add_argument("--reallysend",
                        help="must be specified to really send email", action='store_true')
    PARSER.add_argument("--fileforintrotext",
                        help='friendly text about the script, default is in source file')
    ARGS = PARSER.parse_args()

    # jollyhelper.mail_send_file(toemail=ARGS.toemail,
    #                            subject=ARGS.subject,
    #                            filetosend=ARGS.filetosend,
    #                            filetoattach=ARGS.filetoattach,
    #                            fromname=ARGS.fromname,
    #                            fileforintrotext=ARGS.fileforintrotext,
    #                            filetosaveemail=ARGS.filetosaveemail,
    #                            timedelay=ARGS.timedelay,
    #                            reallysend=ARGS.reallysend)
