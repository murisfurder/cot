#!/usr/bin/env python
#
# edit_product.py - test cases for the COTEditProduct class
#
# January 2015, Glenn F. Matthews
# Copyright (c) 2013-2017 the COT project developers.
# See the COPYRIGHT.txt file at the top-level directory of this distribution
# and at https://github.com/glennmatthews/cot/blob/master/COPYRIGHT.txt.
#
# This file is part of the Common OVF Tool (COT) project.
# It is subject to the license terms in the LICENSE.txt file found in the
# top-level directory of this distribution and at
# https://github.com/glennmatthews/cot/blob/master/LICENSE.txt. No part
# of COT, including this file, may be copied, modified, propagated, or
# distributed except according to the terms contained in the LICENSE.txt file.

"""Unit test cases for the COT.edit_product.COTEditProduct class."""

import re

from COT.commands.tests.command_testcase import CommandTestCase
from COT.commands.edit_product import COTEditProduct
from COT.data_validation import InvalidInputError


class TestCOTEditProduct(CommandTestCase):
    """Unit tests for COTEditProduct command."""

    command_class = COTEditProduct

    def test_readiness(self):
        """Test ready_to_run() under various combinations of parameters."""
        ready, reason = self.command.ready_to_run()
        self.assertFalse(ready)
        self.assertTrue(re.search("No work requested", reason))
        self.assertRaises(InvalidInputError, self.command.run)

        self.command.package = self.input_ovf
        ready, reason = self.command.ready_to_run()
        self.assertFalse(ready)
        self.assertTrue(re.search("No work requested", reason))
        self.assertRaises(InvalidInputError, self.command.run)

        self.command.version = "X"
        ready, reason = self.command.ready_to_run()
        self.assertTrue(ready)

        self.command.version = None
        self.command.full_version = "Y"
        ready, reason = self.command.ready_to_run()
        self.assertTrue(ready)

        self.command.full_version = None
        ready, reason = self.command.ready_to_run()
        self.assertFalse(ready)
        self.assertTrue(re.search("No work requested", reason))
        self.assertRaises(InvalidInputError, self.command.run)

    def test_edit_product_class_no_existing(self):
        """Add a product class where none existed before."""
        self.command.package = self.minimal_ovf
        self.command.product_class = "com.cisco.csr1000v"
        self.command.run()
        self.command.finished()
        self.assertLogged(
            **self.invalid_hardware_warning(None, '0', 'NIC count'))
        self.check_diff(file1=self.minimal_ovf,
                        expected="""
     </ovf:VirtualHardwareSection>
+    <ovf:ProductSection ovf:class="com.cisco.csr1000v">
+      <ovf:Info>Product Information</ovf:Info>
+    </ovf:ProductSection>
   </ovf:VirtualSystem>
""")

    def test_edit_product_class(self):
        """Change the product class."""
        self.command.package = self.iosv_ovf
        self.command.product_class = "com.cisco.ios-xrv9000"
        self.command.run()
        self.command.finished()
        self.assertLogged(**self.invalid_hardware_warning(
            '1CPU-384MB-2NIC', "384", "MiB of RAM"))
        self.assertLogged(**self.invalid_hardware_warning(
            '1CPU-384MB-2NIC', "2", "NIC count"))
        self.assertLogged(**self.invalid_hardware_warning(
            '1CPU-1GB-8NIC', "1024", "MiB of RAM"))
        self.assertLogged(**self.invalid_hardware_warning(
            '1CPU-3GB-10NIC', "3072", "MiB of RAM"))
        self.check_diff(file1=self.iosv_ovf,
                        expected="""
     </ovf:VirtualHardwareSection>
-    <ovf:ProductSection ovf:class="com.cisco.iosv" ovf:instance="1" \
ovf:required="false">
+    <ovf:ProductSection ovf:class="com.cisco.ios-xrv9000" \
ovf:instance="1" ovf:required="false">
       <ovf:Info>Information about the installed software</ovf:Info>
""")

    def test_edit_product_class_noop(self):
        """Setting the product class to itself should do nothing."""
        self.command.package = self.iosv_ovf
        self.command.product_class = "com.cisco.iosv"
        self.command.run()
        self.command.finished()
        self.check_diff(file1=self.iosv_ovf, expected="")

    def test_edit_short_version(self):
        """Editing the short version alone."""
        self.command.package = self.input_ovf
        self.command.version = "5.3.1"
        self.command.run()
        self.command.finished()
        self.check_diff("""
       <ovf:Vendor>VENDOR</ovf:Vendor>
-      <ovf:Version>DEV</ovf:Version>
+      <ovf:Version>5.3.1</ovf:Version>
       <ovf:FullVersion>DEVELOPMENT IMAGE</ovf:FullVersion>
""")

    def test_edit_full_version(self):
        """Editing the full version alone."""
        self.command.package = self.input_ovf
        self.command.full_version = "Cisco IOS XRv, version 3.14159"
        self.command.run()
        self.command.finished()
        self.check_diff("""
       <ovf:Version>DEV</ovf:Version>
-      <ovf:FullVersion>DEVELOPMENT IMAGE</ovf:FullVersion>
+      <ovf:FullVersion>Cisco IOS XRv, version 3.14159</ovf:FullVersion>
       <ovf:ProductUrl>PRODUCT_URL</ovf:ProductUrl>
""")

    def test_edit_product(self):
        """Editing the product alone."""
        self.command.package = self.input_ovf
        self.command.product = "Cisco IOS XRv"
        self.command.run()
        self.command.finished()
        self.check_diff("""
       <ovf:Info>Information about the installed software</ovf:Info>
-      <ovf:Product>PRODUCT</ovf:Product>
+      <ovf:Product>Cisco IOS XRv</ovf:Product>
       <ovf:Vendor>VENDOR</ovf:Vendor>
""")

    def test_edit_product_url(self):
        """Editing the product url alone."""
        self.command.package = self.input_ovf
        self.command.product_url = "http://www.cisco.com/c/en/us/products/\
ios-nx-os-software/ios-xe/index.html"
        self.command.run()
        self.command.finished()
        self.check_diff("""
       <ovf:FullVersion>DEVELOPMENT IMAGE</ovf:FullVersion>
-      <ovf:ProductUrl>PRODUCT_URL</ovf:ProductUrl>
+      <ovf:ProductUrl>http://www.cisco.com/c/en/us/products/\
ios-nx-os-software/ios-xe/index.html</ovf:ProductUrl>
       <ovf:VendorUrl>VENDOR_URL</ovf:VendorUrl>
""")

    def test_edit_vendor(self):
        """Editing the vendor alone."""
        self.command.package = self.input_ovf
        self.command.vendor = "Cisco Systems, Inc."
        self.command.run()
        self.command.finished()
        self.check_diff("""
       <ovf:Product>PRODUCT</ovf:Product>
-      <ovf:Vendor>VENDOR</ovf:Vendor>
+      <ovf:Vendor>Cisco Systems, Inc.</ovf:Vendor>
       <ovf:Version>DEV</ovf:Version>
""")

    def test_edit_vendor_url(self):
        """Editing the vendor url alone."""
        self.command.package = self.input_ovf
        self.command.vendor_url = "http://www.cisco.com"
        self.command.run()
        self.command.finished()
        self.check_diff("""
       <ovf:ProductUrl>PRODUCT_URL</ovf:ProductUrl>
-      <ovf:VendorUrl>VENDOR_URL</ovf:VendorUrl>
+      <ovf:VendorUrl>http://www.cisco.com</ovf:VendorUrl>
       <ovf:AppUrl>APPLICATION_URL</ovf:AppUrl>
""")

    def test_edit_application_url(self):
        """Editing the application url alone."""
        self.command.package = self.input_ovf
        self.command.application_url = "https://router1:530/"
        self.command.run()
        self.command.finished()
        self.check_diff("""
       <ovf:VendorUrl>VENDOR_URL</ovf:VendorUrl>
-      <ovf:AppUrl>APPLICATION_URL</ovf:AppUrl>
+      <ovf:AppUrl>https://router1:530/</ovf:AppUrl>
       <ovf:Category>1. Bootstrap Properties</ovf:Category>
""")

    def test_edit_product_no_existing(self):
        """Edit product in an OVF with no previous values."""
        self.command.package = self.minimal_ovf
        self.command.product = "Product"
        self.command.run()
        self.command.finished()
        self.check_diff(file1=self.minimal_ovf,
                        expected="""
     </ovf:VirtualHardwareSection>
+    <ovf:ProductSection>
+      <ovf:Info>Product Information</ovf:Info>
+      <ovf:Product>Product</ovf:Product>
+    </ovf:ProductSection>
   </ovf:VirtualSystem>
""")

    def test_edit_product_url_no_existing(self):
        """Edit product url in an OVF with no previous values."""
        self.command.package = self.minimal_ovf
        self.command.product_url = "Product URL"
        self.command.run()
        self.command.finished()
        self.check_diff(file1=self.minimal_ovf,
                        expected="""
     </ovf:VirtualHardwareSection>
+    <ovf:ProductSection>
+      <ovf:Info>Product Information</ovf:Info>
+      <ovf:ProductUrl>Product URL</ovf:ProductUrl>
+    </ovf:ProductSection>
   </ovf:VirtualSystem>
""")

    def test_edit_vendor_no_existing(self):
        """Edit vendor in an OVF with no previous values."""
        self.command.package = self.minimal_ovf
        self.command.vendor = "Vendor"
        self.command.run()
        self.command.finished()
        self.check_diff(file1=self.minimal_ovf,
                        expected="""
     </ovf:VirtualHardwareSection>
+    <ovf:ProductSection>
+      <ovf:Info>Product Information</ovf:Info>
+      <ovf:Vendor>Vendor</ovf:Vendor>
+    </ovf:ProductSection>
   </ovf:VirtualSystem>
""")

    def test_edit_vendor_url_no_existing(self):
        """Edit vendor url in an OVF with no previous values."""
        self.command.package = self.minimal_ovf
        self.command.vendor_url = "Vendor URL"
        self.command.run()
        self.command.finished()
        self.check_diff(file1=self.minimal_ovf,
                        expected="""
     </ovf:VirtualHardwareSection>
+    <ovf:ProductSection>
+      <ovf:Info>Product Information</ovf:Info>
+      <ovf:VendorUrl>Vendor URL</ovf:VendorUrl>
+    </ovf:ProductSection>
   </ovf:VirtualSystem>
""")

    def test_edit_application_url_no_existing(self):
        """Edit application url in an OVF with no previous values."""
        self.command.package = self.minimal_ovf
        self.command.application_url = "Application URL"
        self.command.run()
        self.command.finished()
        self.check_diff(file1=self.minimal_ovf,
                        expected="""
     </ovf:VirtualHardwareSection>
+    <ovf:ProductSection>
+      <ovf:Info>Product Information</ovf:Info>
+      <ovf:AppUrl>Application URL</ovf:AppUrl>
+    </ovf:ProductSection>
   </ovf:VirtualSystem>
""")

    def test_edit_full_no_existing(self):
        """Edit full version in an OVF with no previous values."""
        self.command.package = self.minimal_ovf
        self.command.full_version = "Full Version"
        self.command.run()
        self.command.finished()
        self.check_diff(file1=self.minimal_ovf,
                        expected="""
     </ovf:VirtualHardwareSection>
+    <ovf:ProductSection>
+      <ovf:Info>Product Information</ovf:Info>
+      <ovf:FullVersion>Full Version</ovf:FullVersion>
+    </ovf:ProductSection>
   </ovf:VirtualSystem>
""")

    def test_edit_all(self):
        """Edit all product section strings."""
        self.command.package = self.input_ovf
        self.command.product_class = ''
        self.command.version = "5.2.0.01I"
        self.command.full_version = "Cisco IOS XRv, Version 5.2"
        self.command.product = "Cisco IOS XRv"
        self.command.product_url = "http://www.cisco.com/c/en/us/products\
/ios-nx-os-software/ios-xe/index.html"
        self.command.vendor = "Cisco Systems, Inc."
        self.command.vendor_url = "http://www.cisco.com"
        self.command.application_url = "https://router1:530/"
        self.command.run()
        self.assertLogged(**self.UNRECOGNIZED_PRODUCT_CLASS)
        self.command.finished()
        self.check_diff("""
     </ovf:VirtualHardwareSection>
-    <ovf:ProductSection ovf:required="false">
+    <ovf:ProductSection ovf:class="" ovf:required="false">
       <ovf:Info>Information about the installed software</ovf:Info>
-      <ovf:Product>PRODUCT</ovf:Product>
-      <ovf:Vendor>VENDOR</ovf:Vendor>
-      <ovf:Version>DEV</ovf:Version>
-      <ovf:FullVersion>DEVELOPMENT IMAGE</ovf:FullVersion>
-      <ovf:ProductUrl>PRODUCT_URL</ovf:ProductUrl>
-      <ovf:VendorUrl>VENDOR_URL</ovf:VendorUrl>
-      <ovf:AppUrl>APPLICATION_URL</ovf:AppUrl>
+      <ovf:Product>Cisco IOS XRv</ovf:Product>
+      <ovf:Vendor>Cisco Systems, Inc.</ovf:Vendor>
+      <ovf:Version>5.2.0.01I</ovf:Version>
+      <ovf:FullVersion>Cisco IOS XRv, Version 5.2</ovf:FullVersion>
+      <ovf:ProductUrl>http://www.cisco.com/c/en/us/products/\
ios-nx-os-software/ios-xe/index.html</ovf:ProductUrl>
+      <ovf:VendorUrl>http://www.cisco.com</ovf:VendorUrl>
+      <ovf:AppUrl>https://router1:530/</ovf:AppUrl>
       <ovf:Category>1. Bootstrap Properties</ovf:Category>
""")

    def test_edit_all_no_existing(self):
        """Edit all product section strings with no previous values."""
        self.command.package = self.minimal_ovf
        self.command.product_class = "foobar"
        self.command.version = "Version"
        self.command.full_version = "Full Version"
        self.command.product = "Product"
        self.command.product_url = "Product URL"
        self.command.vendor = "Vendor"
        self.command.vendor_url = "Vendor URL"
        self.command.application_url = "Application URL"
        self.command.run()
        self.assertLogged(**self.UNRECOGNIZED_PRODUCT_CLASS)
        self.command.finished()
        self.check_diff(file1=self.minimal_ovf,
                        expected="""
     </ovf:VirtualHardwareSection>
+    <ovf:ProductSection ovf:class="foobar">
+      <ovf:Info>Product Information</ovf:Info>
+      <ovf:Product>Product</ovf:Product>
+      <ovf:Vendor>Vendor</ovf:Vendor>
+      <ovf:Version>Version</ovf:Version>
+      <ovf:FullVersion>Full Version</ovf:FullVersion>
+      <ovf:ProductUrl>Product URL</ovf:ProductUrl>
+      <ovf:VendorUrl>Vendor URL</ovf:VendorUrl>
+      <ovf:AppUrl>Application URL</ovf:AppUrl>
+    </ovf:ProductSection>
   </ovf:VirtualSystem>
""")
