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

mgmt_node = sys.argv[1]
local_node = sys.argv[2]
local_site = sys.argv[3]
remote_site = sys.argv[4]

client = etcd.Client(mgmt_node, 4000)

def describe_clusters():
    # Pull out all the clearwater keys.
    key = "/?recursive=True"

    try:
        result = client.get(key)
    except etcd.EtcdKeyNotFound:
        # There's no clearwater keys yet
        return

    cluster_values = {subkey.key: subkey.value for subkey in result.leaves}

    for (key, value) in sorted(cluster_values.items()):
        # Check if the key relates to clustering. The clustering key has the format
        # /clearwater*[</optional site name>]/<node type>/clustering/<store type>
        key_parts = key.split('/')

        if len(key_parts) > 5 and key_parts[4] == 'clustering':
            site = key_parts[2]
            node_type = key_parts[3]
            store_name = key_parts[5]
        elif len(key_parts) > 4 and key_parts[3] == 'clustering':
            site = ""
            node_type = key_parts[2]
            store_name = key_parts[4]
        else:
            # The key isn't to do with clustering, skip it
            continue

        if site != "" and remote_site != "":
            print "Describing the {} {} cluster in site {}:".format(node_type.capitalize(), store_name.capitalize(), site)
        else:
            print "Describing the {} {} cluster:".format(node_type.capitalize(), store_name.capitalize())

        cluster = json.loads(value)
        cluster_ok = all([state == "normal"
                          for node, state in cluster.iteritems()])

        if local_node in cluster:
            print "  The local node is in this cluster"
        else:
            print "  The local node is *not* in this cluster"

        if cluster_ok:
            print "  The cluster is stable"
        else:
            print "  The cluster is *not* stable"

        for node, state in cluster.iteritems():
            print "    {} is in state {}".format(node, state)
        print ""

describe_clusters()
