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
######################################################################

def PortalFactory(content, operation):
    """
    filter any transient content in portal factory
    """
    # a simple check for factory in absolute url breaks portal factory..
    # no comment :-) as an alternative walk the chain.
    chain = getattr(content, 'aq_chain', None)

    if not chain:
        return

    for ob in chain[:-1]: # slice out request
        if ob.__name__ == 'portal_factory':
            operation.filtered = True
            return
