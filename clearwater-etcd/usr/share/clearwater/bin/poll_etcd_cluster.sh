#!/bin/bash

# @file poll_etcd_cluster.sh
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

# This script is used by Monit to check connectivity to remote etcd instances.
# If connectivity is lost to any instances in the cluster an alarm will be
# issued (major severity for a single instance, critical severity if enough
# instances are unreachable that quorum can't be formed). When connectivity is
# restored to all instances, the alarm is cleared. Alarms are issued here vs.
# the Monit DSL to avoid retransmissions.
#
# Execution of etcdctl is "niced" to minimize the impact of its use.

alarm_state_file="/tmp/.clearwater_etcd_alarm_issued"

. /etc/clearwater/config
export ETCDCTL_PEERS=http://${management_local_ip:-$local_ip}:4000

# Return state of the etcd cluster, 0 if all nodes are up, 1 if some nodes are
# down, 2 if quorum has failed.
cluster_state()
{
    # Run etcdctl to get the status of the cluster, if successful continue to
    # check output, otherwise return 0 (local etcd failure is not considered a
    # cluster error).
    local out=`nice -n 19 etcdctl cluster-health 2> /dev/null`
    if [ "$?" = 0 ] ; then
      local unhealthy_cluster_state_regex="cluster is unhealthy"
      if [[ $out =~ $unhealthy_cluster_state_regex ]]
      then
        return 2
      fi

      local maybe_unhealthy_cluster_state_regex="cluster may be unhealthy"
      if [[ $out =~ $maybe_unhealthy_cluster_state_regex ]]
      then
        return 2
      fi

      IFS=$'\n'
      # The output of cluster-health can report the following:
      #   Member is healthy
      #   Member is unhealthy
      #   Member is unreachable :: we don't treat this as an alarmable condition atm
      local unhealthy_node_regex="member [a-zA-Z0-9]* is unhealthy"
      local healthy_node_regex="member [a-zA-Z0-9]* is healthy"
      for line in $out
      do
        if [[ $line =~ $unhealthy_node_regex ]]
        then
          unhealthy_members=true
        elif [[ $line =~ $healthy_node_regex ]]
        then
          parse_member_ip $line
        fi
      done
      if [ $unhealthy_members ]
      then
        return 1
      fi
    fi
    return 0
}

parse_member_ip()
{
    # The output of cluter health looks like:
    # member <member_id> is healthy: got healthy result from http://<member_ip>:4000
    # We want to pull out the ip, to build an up to date etcd_cluster value
    # The steps are:
    #   select the ninth section: http://<member_ip>:4000
    #   strip the 'http://' from the front
    #   cut the ':4000' from the end
    member_ip=$( echo $1 | cut -d " " -f 9 | sed 's/http:\/\///' | cut -d : -f 1 )
    echo Member ip is $member_ip
    HEALTHY_MEMBER_LIST=$member_ip,$HEALTHY_MEMBER_LIST
}


check_clear_alarm()
{
    if [ -f $alarm_state_file ] ; then
        rm -f $alarm_state_file
        /usr/share/clearwater/bin/issue-alarm "monit" "6501.1"
    fi
}


check_issue_major_alarm()
{
    if [ ! -f $alarm_state_file ] || [ `cat $alarm_state_file` != "major" ] ; then
        echo "major" > $alarm_state_file
        /usr/share/clearwater/bin/issue-alarm "monit" "6501.4"
    fi
}


check_issue_critial_alarm()
{
    if [ ! -f $alarm_state_file ] || [ `cat $alarm_state_file` != "critical" ] ; then
        echo "critical" > $alarm_state_file
        /usr/share/clearwater/bin/issue-alarm "monit" "6501.3"
    fi
}


cluster_state
state=$?

echo $state

if [ "$state" = 0 ] ; then
    # add the list of healthy mambers to a state file, so we can rejoin safely if we die
    echo "etcd_cluster=$HEALTHY_MEMBER_LIST" > "/etc/clearwater/healthy_etcd_members"
    check_clear_alarm
elif [ "$state" = 1 ] ; then
    check_issue_major_alarm
else
    check_issue_critial_alarm
fi

exit $state

