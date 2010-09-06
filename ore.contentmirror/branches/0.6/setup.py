import os
from setuptools import setup, find_packages

VERSION = "0.6.0-rc3"


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name="ore.contentmirror",
    version=VERSION,
    url="http://contentmirror.googlecode.com",
    install_requires=["setuptools",
                      "SQLAlchemy==0.5.8",
                      "zope.sqlalchemy",
                      "zope.component",
                      "zope.event",
                      "zope.schema"],
#                      "zope.app.container",
#                      "zope.app.event",
#                      "zope.configuration"
#                      "zope.security",
#                      "zope.app.component",
#                      "ZODB3",
    packages=find_packages(exclude=["*.tests"]),
    namespace_packages=["ore"],
    include_package_data=True,
    package_data = {
      "": ["*.txt", "*.zcml"],
      "ore.contentmirror": ["*.zcml", "*.txt"]},
    zip_safe=False,
    author="Kapil Thangavelu",
    author_email="kapil.foss@gmail.com",
    description="Deploy Content from Plone to a Relational Database",
    long_description=read("ore", "contentmirror", "readme.txt"),
    license="GPL",
    keywords="plone zope zope3",
    entry_points={
     "console_scripts": ["mirror-ddl = ore.contentmirror.ddl:main",
                         "mirror-bulk = ore.contentmirror.bulk:main"],
        }
    )
