#!/usr/bin/env python
#
# gcc.py - Helper for 'gcc'
#
# October 2016, Glenn F. Matthews
# Copyright (c) 2013-2016 the COT project developers.
# See the COPYRIGHT.txt file at the top-level directory of this distribution
# and at https://github.com/glennmatthews/cot/blob/master/COPYRIGHT.txt.
#
# This file is part of the Common OVF Tool (COT) project.
# It is subject to the license terms in the LICENSE.txt file found in the
# top-level directory of this distribution and at
# https://github.com/glennmatthews/cot/blob/master/LICENSE.txt. No part
# of COT, including this file, may be copied, modified, propagated, or
# distributed except according to the terms contained in the LICENSE.txt file.

"""Give COT access to ``gcc`` command for building other helpers."""

from COT.helpers.helper import Helper


class GCC(Helper):
    """Helper provider for ``gcc`` command."""

    _provider_package = {
        'apt-get': 'gcc',
        'yum': 'gcc',
    }

    def __init__(self):
        """Initializer."""
        super(GCC, self).__init__("gcc")
