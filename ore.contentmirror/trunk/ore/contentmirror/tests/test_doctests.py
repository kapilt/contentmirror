####################################################################
# Copyright (c) Kapil Thangavelu. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
####################################################################

"""
$Id: $
"""

import unittest
import os
from zope.testing import doctest
from base import setUp, tearDown, doctest_ns

optionflags = (
    doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS |
    doctest.REPORT_ONLY_FIRST_FAILURE)


def test_suite():
    if os.environ.get("NO_DOC"):
        return unittest.TestSuite()

    return unittest.TestSuite((
        doctest.DocFileSuite(
            'readme.txt',
            package="ore.contentmirror",
            setUp=setUp, tearDown=tearDown,
            optionflags=optionflags,
            globs=doctest_ns),
        doctest.DocFileSuite(
            'ref.txt',
            package="ore.contentmirror",
            setUp=setUp, tearDown=tearDown,
            optionflags=optionflags,
            globs=doctest_ns),
    ))
