# @file test_chronos_gr_config_plugin.py
#
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

import unittest
import mock
import logging

_log = logging.getLogger()

from clearwater_etcd_plugins.chronos.chronos_gr_config_plugin import ChronosGRConfigPlugin

class TestConfigManagerPlugin(unittest.TestCase):
    @mock.patch('clearwater_etcd_plugins.chronos.chronos_gr_config_plugin.safely_write')
    @mock.patch('clearwater_etcd_plugins.chronos.chronos_gr_config_plugin.run_command')
    def test_chronos_gr_config_changed(self, mock_run_command, mock_safely_write):
        """Test Chronos GR Config plugin writes new config when config has changed"""

        # Create the plugin
        plugin = ChronosGRConfigPlugin({})

        # Set up the config strings to be tested
        old_config_string = "Old Chronos GR config"
        new_config_string = "New Chronos GR config"

        # Call 'on_config_changed' with file.open mocked out
        with mock.patch('clearwater_etcd_plugins.chronos.chronos_gr_config_plugin.open', \
             mock.mock_open(read_data=old_config_string), create=True) as mock_open:
            plugin.on_config_changed(new_config_string, None)

        # Test assertions
        mock_open.assert_called_once_with(plugin.file(), "r")
        mock_safely_write.assert_called_once_with(plugin.file(), new_config_string)
        mock_run_command.assert_called_once_with("/usr/share/clearwater/clearwater-queue-manager/scripts/modify_nodes_in_queue add apply_chronos_gr_config")
