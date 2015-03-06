#!/usr/bin/env python
#
# deploy.py - test cases for the COTDeploy and COTDeployESXi classes
#
# January 2015, Glenn F. Matthews
# Copyright (c) 2013-2015 the COT project developers.
# See the COPYRIGHT.txt file at the top-level directory of this distribution
# and at https://github.com/glennmatthews/cot/blob/master/COPYRIGHT.txt.
#
# This file is part of the Common OVF Tool (COT) project.
# It is subject to the license terms in the LICENSE.txt file found in the
# top-level directory of this distribution and at
# https://github.com/glennmatthews/cot/blob/master/LICENSE.txt. No part
# of COT, including this file, may be copied, modified, propagated, or
# distributed except according to the terms contained in the LICENSE.txt file.

import getpass
import logging
import re

from distutils.version import StrictVersion

from COT.tests.ut import COT_UT
from COT.ui_shared import UI
import COT.helper_tools
import COT.deploy
from COT.deploy import COTDeploy, COTDeployESXi
from COT.data_validation import InvalidInputError

logger = logging.getLogger(__name__)


class TestCOTDeploy(COT_UT):

    def setUp(self):
        "Test case setup function called automatically prior to each test"
        super(TestCOTDeploy, self).setUp()
        self.instance = COTDeploy(UI())
        self.instance.package = self.input_ovf

    def test_not_ready_with_no_args(self):
        ready, reason = self.instance.ready_to_run()
        self.assertEqual(ready, False)
        self.assertTrue(re.search("HYPERVISOR.*mandatory", reason))
        self.assertRaises(InvalidInputError, self.instance.run)

        self.instance.hypervisor = "esxi"
        self.instance.package = None
        ready, reason = self.instance.ready_to_run()
        self.assertEqual(ready, False)
        self.assertTrue(re.search("PACKAGE.*mandatory", reason))
        self.assertRaises(InvalidInputError, self.instance.run)

    def test_invalid_args(self):
        with self.assertRaises(InvalidInputError):
            self.instance.hypervisor = "frobozz"
        with self.assertRaises(InvalidInputError):
            self.instance.configuration = ""
        with self.assertRaises(InvalidInputError):
            self.instance.configuration = "X"


class TestCOTDeployESXi(COT_UT):

    # Some WARNING logger messages we may expect at various points:
    SERIAL_PORT_FIXUP = {
        'levelname': 'WARNING',
        'msg': 'Package.*2 serial ports.*must add them manually',
    }
    VSPHERE_ENV_WARNING = {
        'levelname': 'WARNING',
        'msg': "deploying.*vSphere.*power-on.*environment properties.*ignored",
    }
    OVFTOOL_VER_TOO_LOW = {
        'levelname': 'WARNING',
        'msg': "ovftool version is too low.*environment properties.*ignored",
    }

    def stub_check_call(self, argv, require_success=True):
        logger.info("stub_check_call({0}, {1})".format(argv, require_success))
        if argv[0] == 'ovftool':
            self.last_argv = argv
            logger.info("Caught ovftool invocation")
            return
        return self._check_call(argv, require_success)

    def stub_check_output(self, argv, require_success=True):
        logger.info("stub_check_output({0}, {1}".format(argv, require_success))
        if argv[0] == 'ovftool' and argv[1] == '--version':
            logger.info("Caught 'ovftool --version' invocation")
            return "VMware ovftool {0}".format(self.ovftool_version)
        return self._check_output(argv, require_success)

    def setUp(self):
        "Test case setup function called automatically prior to each test"
        super(TestCOTDeployESXi, self).setUp()
        self.instance = COTDeployESXi(UI())
        self.instance.package = self.input_ovf
        self.instance.hypervisor = 'esxi'
        # Stub out check_call so that we don't actually need ovftool
        self._check_call = COT.deploy.check_call
        self.last_argv = []
        COT.deploy.check_call = self.stub_check_call
        # Ditto
        self._ovftool_version = COT.helper_tools.OVFTOOL_VERSION
        COT.helper_tools.OVFTOOL_VERSION = None
        self.ovftool_version = StrictVersion("4.0.0")
        self._check_output = COT.helper_tools.check_output
        COT.helper_tools.check_output = self.stub_check_output

    def tearDown(self):
        "Test case cleanup function called automatically"
        # Remove our stub
        COT.deploy.check_call = self._check_call
        COT.helper_tools.check_output = self._check_output
        COT.helper_tools.OVFTOOL_VERSION = self._ovftool_version
        super(TestCOTDeployESXi, self).tearDown()

    def test_not_ready_with_no_args(self):
        ready, reason = self.instance.ready_to_run()
        self.assertEqual(ready, False)
        self.assertTrue(re.search("LOCATOR.*mandatory", reason))
        self.assertRaises(InvalidInputError, self.instance.run)

        self.instance.locator = "localhost"
        self.instance.package = None
        ready, reason = self.instance.ready_to_run()
        self.assertEqual(ready, False)
        self.assertTrue(re.search("PACKAGE.*mandatory", reason))
        self.assertRaises(InvalidInputError, self.instance.run)

    def test_invalid_args(self):
        with self.assertRaises(InvalidInputError):
            self.instance.configuration = ""
        with self.assertRaises(InvalidInputError):
            self.instance.configuration = "X"
        with self.assertRaises(InvalidInputError):
            self.instance.power_on = "frobozz"

    def test_ovftool_args_basic(self):
        "Test that ovftool is called with the expected arguments"
        self.instance.locator = "localhost"
        self.instance.run()
        self.assertEqual([
            'ovftool',
            '--deploymentOption=4CPU-4GB-3NIC',    # default configuration
            self.input_ovf,
            'vi://{user}:passwd@localhost'.format(user=getpass.getuser())
        ], self.last_argv)
        self.assertLogged(**self.VSPHERE_ENV_WARNING)
        self.assertLogged(**self.SERIAL_PORT_FIXUP)

    def test_ovftool_args_advanced(self):
        "Test that ovftool is called with the expected arguments"
        self.instance.locator = "localhost/host/foo"
        self.instance.datastore = "datastore1"
        self.instance.configuration = "2CPU-2GB-1NIC"
        self.instance.vm_name = "myVM"
        self.instance.power_on = True
        self.instance.ovftool_args = "--overwrite --vService:'A B=C D'"
        self.instance.username = "u"
        self.instance.password = "p"
        self.instance.network_map = ["VM Network=VM Network"]

        self.instance.run()
        self.assertEqual([
            'ovftool',
            '--overwrite',
            '--vService:A B=C D',
            '--deploymentOption=2CPU-2GB-1NIC',
            '--net:VM Network=VM Network',
            '--name=myVM',
            '--powerOn',
            '--datastore=datastore1',
            self.input_ovf,
            'vi://u:p@localhost/host/foo',
        ], self.last_argv)
        self.assertLogged(**self.SERIAL_PORT_FIXUP)

    def test_ovftool_vsphere_env_fixup(self):
        "Test fixup of environment when deploying directly to vSphere"

        # With 4.0.0 (our default) and no power_on, there's no fixup.
        # This is tested by test_ovftool_args_basic() above.

        # With 4.0.0 and power_on, we fixup when deploying to vSphere:
        self.instance.locator = "vsphere"
        self.instance.power_on = True
        self.instance.run()
        self.assertEqual([
            'ovftool',
            '--X:injectOvfEnv',
            '--deploymentOption=4CPU-4GB-3NIC',     # default configuration
            '--powerOn',
            self.input_ovf,
            'vi://{user}:passwd@vsphere'.format(user=getpass.getuser()),
        ], self.last_argv)
        self.assertLogged(**self.SERIAL_PORT_FIXUP)
        # Make sure we DON'T see the ENV_WARNING message
        self.logging_handler.assertNoLogsOver(logging.INFO)

        # With 4.0.0, we don't (need to) fixup when deploying to vCenter.
        # This is tested by test_ovftool_args_advanced() above.

        # With <4.0.0, we don't (can't) fixup, regardless.
        # Discard cached information and update the info that will be returned
        COT.helper_tools.OVFTOOL_VERSION = None
        self.ovftool_version = StrictVersion("3.5.0")
        self.instance.run()
        self.assertEqual([
            'ovftool',
            # Nope! #'--X:injectOvfEnv',
            '--deploymentOption=4CPU-4GB-3NIC',     # default configuration
            '--powerOn',
            self.input_ovf,
            'vi://{user}:passwd@vsphere'.format(user=getpass.getuser()),
        ], self.last_argv)
        self.assertLogged(**self.OVFTOOL_VER_TOO_LOW)
        self.assertLogged(**self.SERIAL_PORT_FIXUP)