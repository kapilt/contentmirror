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
from zope import component

import interfaces

from plonegine.main import ATFolder, ATBTreeFolder, ATDocument, ATFavorite, ATLink, ATNewsItem, ATImage, ATFile, ATEvent

Content = {
           'Folder':ATFolder,
           'Large Plone Folder':ATBTreeFolder,
           'Document':ATDocument,
           'Favorite':ATFavorite,
           'Link':ATLink,
           'News Item':ATNewsItem,
           'Image':ATImage,
           'File':ATFile,
           'Event':ATEvent,
          }

def fromUID( content_uid ):
    store = component.getUtility( interfaces.IAppEngine, 'appengine')
    peers = store.db.GqlQuery("select * from PloneContent where uid=:1",content_uid).fetch(1)
    if peers:
        return peers[0]
    return None
