#! /usr/bin/python
# @file load_from_chronos_cluster.py
#
# Project Clearwater - IMS in the Cloud
# Copyright (C) 2015  Metaswitch Networks Ltd
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

import sys
import etcd
import json
import os

local_ip = sys.argv[1]
site_name = sys.argv[2]
node_type = sys.argv[3]
etcd_key = sys.argv[4]

assert os.path.exists("/etc/init.d/chronos"), \
    "This script should be run on a node that's running Chronos"

etcd_key = "/{}/{}/{}/clustering/chronos".format(etcd_key, site_name, node_type)

with open('/etc/chronos/chronos_cluster.conf') as f:
    nodes = {}

    for line in f.readlines():
        line = line.strip().replace(' ','')
        if '=' in line:
            key, value = line.split("=")
            if key == "node":
                nodes[value] = "normal"
            elif key == "leaving":
                nodes[value] = "leaving"
            elif key == "joining":
                nodes[value] = "joining"

    data = json.dumps(nodes)

print "Inserting data %s into etcd key %s" % (data, etcd_key)

c = etcd.Client(local_ip, 4000)
new = c.write(etcd_key, data).value

if new == data:
    print "Update succeeded"
else:
    print "Update failed"
