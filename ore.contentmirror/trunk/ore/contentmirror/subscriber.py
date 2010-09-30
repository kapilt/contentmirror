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

import interfaces


def objectAdded(object, event):
    operations = interfaces.IOperationFactory(object, None)
    if operations:
        operations.add()


def objectModified(object, event):
    operations = interfaces.IOperationFactory(object, None)
    if operations:
        operations.update()


def objectDeleted(object, event):
    operations = interfaces.IOperationFactory(object, None)
    if operations:
        operations.delete()


def objectMoved(object, event):
    operations = interfaces.IOperationFactory(object, None)
    if operations:
        operations.move()


def containerReordered(object, event):
    operations = interfaces.IOperationFactory(object, None)
    if operations:
        import pdb; pdb.set_trace()
        operations.reposition()
