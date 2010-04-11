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
Testing Infrastructure
"""
import time
import unittest
import random
import md5
import os
import sqlalchemy
import transaction

from cStringIO import StringIO

from zope import interface, component
from zope.component import testing as placelesssetup
from zope.configuration.xmlconfig import xmlconfig, XMLConfig
from zope.component.tests import clearZCML

from ore import contentmirror
from ore.contentmirror import (
    interfaces, transform, peer, serializer, schema, operation, session)

interface.classImplements(sqlalchemy.MetaData, interfaces.IMetaData)


def setUp(test):
    placelesssetup.setUp()
    component.provideAdapter(transform.StringTransform)
    component.provideAdapter(transform.IntegerTransform)
    component.provideAdapter(transform.FloatTransform)
    component.provideAdapter(transform.DateTimeTransform)
    component.provideAdapter(transform.LinesTransform)
    component.provideAdapter(transform.BooleanTransform)
    component.provideAdapter(transform.FileTransform)
    component.provideAdapter(transform.PhotoTransform)
    component.provideAdapter(transform.ReferenceTransform)

    component.provideUtility(peer.PeerRegistry())
    component.provideAdapter(
        peer.PeerFactory,
        (interfaces.IMirrored, interfaces.ISchemaTransformer))

    component.provideAdapter(transform.SchemaTransformer,
                             (interfaces.IMirrored, interfaces.IMetaData))
    component.provideAdapter(serializer.Serializer, (interfaces.IMirrored,))
    component.provideAdapter(
        operation.OperationFactory, (interfaces.IMirrored,))
    component.provideUtility(operation.OperationBufferFactory())


def tearDown(test):
    placelesssetup.tearDown()
    transaction.abort()
    schema.metadata.drop_all(checkfirst=True)


def reset_db():
    tables = schema.metadata.sorted_tables
    tables.reverse()
    for i in tables:
        i.drop(checkfirst=True)
    schema.metadata.create_all(checkfirst=True)


def test_db_uri():
    db_uri = os.environ.get('CONTENTMIRROR_URI')
    if db_uri is None:
        db_uri = 'sqlite://'
    return db_uri


class IntegrationTestCase(unittest.TestCase):

    sample_content = "ore.contentmirror.tests.base.SampleContent"
    custom_content = "ore.contentmirror.tests.base.CustomContent"

    def setUp(self):
        setUp(self)
        XMLConfig("meta.zcml", component)()
        XMLConfig("meta.zcml", contentmirror)()
        XMLConfig("base.zcml", contentmirror)()
        schema.metadata.bind = sqlalchemy.create_engine(test_db_uri())
        schema.metadata.create_all(checkfirst=True)

    def tearDown(self):
        tearDown(self)
        clearZCML()
        schema.metadata.drop_all(checkfirst=True)
        session.Session().expunge_all()

    def _load(self, text):
        template = """\
        <configure xmlns='http://namespaces.zope.org/zope'
                   xmlns:ore='http://namespaces.objectrealms.net/mirror'
                   i18n_domain='mirror'>
        %s
        </configure>"""
        xmlconfig(StringIO(template % text))


def make_uuid(*args):
    t = str(time.time() * 1000L)
    r = str(random.random()*100000000000000000L)
    data = t +' '+ r +' '+ \
           str(random.random()*100000000000000000L)+' '+ str(args)
    uid = md5.md5(data).hexdigest()
    return uid


class WorkflowTool(object):

    def getCatalogVariablesFor(self, instance):
        return {'review_state':
                getattr(instance, 'workflow_state', 'published')}


class URLTool(object):

    def getRelativeContentPath(self, instance):
        return instance.getPhysicalPath()


class Jar(object):

    def incrgc(self):
        return

    @property
    def _cache(self):
        return self


class BaseContent(object):

    portal_type = ""
    schema = None

    portal_workflow = WorkflowTool()
    portal_url = URLTool()

    _p_jar = Jar()

    def __init__(self, id, container=None, **kw):
        self.id = id
        self.uid = make_uuid(id)

        for k, v in kw.items():
            if k in self.schema:
                setattr(self, k, v)

        self.container = container

    @property
    def __name__(self):
        return self.id

    @property
    def __parent__(self):
        return self.container

    @property
    def aq_chain(self):
        chain = [self]
        if self.container:
            parent_chain = self.container.aq_chain
            if parent_chain:
                chain.extend(parent_chain)
        else:
            return None
        return filter(None, chain)

    def Schema(self):
        return self.schema

    def UID(self):
        return self.uid

    def getParentNode(self):
        return self.container

    def getPhysicalPath(self):
        path = []
        ob = self
        while True:
            path.append(ob. id)
            ob = ob.container
            if ob is None:
                break
        path.reverse()
        return path


class Schema(object):

    def __init__(self, fields):
        self._fields = fields

    def fields(self):
        return self._fields

    def __contains__(self, name):
        for f in self._fields:
            if f.__name__ == name:
                return True


class DateTime(object):
    # mock zope2 datetime
    def __init__(self):
        self.value = time.time()

    def timeTime(self):
        return self.value


class File(object):

    def __init__(self, id, content, mime_type="text/plain"):
        self.id = id
        self.data = content
        self.mime_type = mime_type

    def getId(self):
        return self.id


class MockField(object):

    defaults = {'required': False,
                'default': '',
                'vocabulary': '',
                'schemata': 'default'}

    def __init__(self, name=None, **kw):

        self.__name__ = name
        # copy
        values = dict(self.defaults)
        values.update(kw)
        self.__dict__.update(values)

    def getAccessor(self, instance):
        return lambda: getattr(instance,
                                self.__name__,
                                self.default)


class StringField(MockField):
    interface.implements(interfaces.IStringField)


class IntegerField(MockField):
    interface.implements(interfaces.IIntegerField)


class FloatField(MockField):
    interface.implements(interfaces.IFloatField)


class ReferenceField(MockField):
    multiValued = True
    interface.implements(interfaces.IReferenceField)


class LinesField(MockField):
    interface.implements(interfaces.ILinesField)


class TextField(MockField):
    interface.implements(interfaces.ITextField)


class FileField(MockField):
    interface.implements(interfaces.IFileField)

    def getContentType(self, instance):
        return self.getAccessor(instance)().mime_type


class BooleanField(MockField):
    interface.implements(interfaces.IBooleanField)


class ImageField(MockField):
    interface.implements(interfaces.IImageField)


class DateTimeField(MockField):
    interface.implements(interfaces.IDateTimeField)


class PhotoField(MockField):
    interface.implements(interfaces.IPhotoField)


class SampleContent(BaseContent):
    portal_type = "Sample Content"
    interface.implements(interfaces.IMirrored)
    schema = Schema((StringField("stuff"),
                     DateTimeField("modification_date")))


class CustomContent(object):
    """
    Content which does not implement IMirrored by default.
    """
    schema = Schema(())

    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return "<CustomContent %r>"%(self.id)

    def Schema(self):
        return self.schema

    def UID(self):
        return "21"



doctest_ns = {
    'IntegerField'  : IntegerField,
    'FloatField'    : FloatField,
    'TextField'     : TextField,
    'StringField'   : StringField,
    'FileField'     : FileField,
    'ImageField'    : ImageField,
    'DateTimeField' : DateTimeField,
    'ReferenceField': ReferenceField,
    'LinesField'    : LinesField,
    'BaseContent'   : BaseContent,
    'Schema'        : Schema,
    'DateTime'      : DateTime,
    'File'          : File,
    'test_db_uri'   : test_db_uri,
    'reset_db'      : reset_db}
