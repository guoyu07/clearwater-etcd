# Project Clearwater - IMS in the Cloud
# Copyright (C) 2016 Metaswitch Networks Ltd
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version, along with the "Special Exception" for use of
# the program along with SSL, set forth below. This program is distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details. You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
# The author can be reached by email at clearwater@metaswitch.com or by
# post at Metaswitch Networks Ltd, 100 Church St, Enfield EN2 6BQ, UK
#
# Special Exception
# Metaswitch Networks Ltd  grants you permission to copy, modify,
# propagate, and distribute a work formed by combining OpenSSL with The
# Software, or a work derivative of such a combination, even if such
# copying, modification, propagation, or distribution would otherwise
# violate the terms of the GPL. You must comply with the GPL in all
# respects for all of the code used other than OpenSSL.
# "OpenSSL" means OpenSSL toolkit software distributed by the OpenSSL
# Project and licensed under the OpenSSL Licenses, or a work based on such
# software and licensed under the OpenSSL Licenses.
# "OpenSSL Licenses" means the OpenSSL License and Original SSLeay License
# under which the OpenSSL Project distributes the OpenSSL toolkit software,
# as those licenses appear in the file LICENSE-OPENSSL.

import os
import sys
import json
import difflib
import subprocess
import syslog

def main():
    # URL of shared_config etcd key
    url = sys.argv[1]

    # Get the old shared_config stored on etcd
    # If this fails, this script is the least of our worries and we ignore, because
    # upload_shared_config, which called this script, will print an error instead
    jsonstr = subprocess.check_output(["curl", "-s", "-X", "GET", url])

    new_config_lines = open("/etc/clearwater/shared_config").read().splitlines()
    # etcd returns JSON; the shared_config is in node.value
    old_config_lines = json.loads(jsonstr)["node"]["value"].splitlines()

    # We're looking to log meaningful configuration changes, so sort the lines to
    # ignore changes in line ordering
    new_config_lines.sort()
    old_config_lines.sort()
    difflines = list(difflib.ndiff(old_config_lines, new_config_lines))

    # Pull out lines prefixed by "+ " / "- ", wrap in quotes, concatenate, and
    # delete trailing comma
    additions = ''.join(("\"" + line[2:] + "\", ") for line in difflines \
        if line.startswith("+ ")).rstrip(", ")
    deletions = ''.join(("\"" + line[2:] + "\", ") for line in difflines \
        if line.startswith("- ")).rstrip(", ")

    # We'll be running as root, but SUDO_USER pulls out the user who invoked sudo
    username = os.environ['SUDO_USER']

    if additions or deletions:
        logstr = "Configuration file change: the file shared_config was modified by user {}. ".format(username)
        if deletions:
            logstr += "LINES REMOVED: "
            logstr += deletions + ". "
        if additions:
            logstr += "LINES ADDED: "
            logstr += additions + "."

        print logstr

        # Log the changes
        syslog.openlog("Audit", syslog.LOG_PID)
        syslog.syslog(syslog.LOG_NOTICE, logstr)
        syslog.closelog()

main()
