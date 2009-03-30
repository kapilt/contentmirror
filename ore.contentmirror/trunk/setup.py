import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name="ore.contentmirror",
    version="0.5-dev",
    url="http://contentmirror.googlecode.com",
    download_url="http://code.google.com/p/contentmirror/downloads/list",
    install_requires=['setuptools',
                      'SQLAlchemy>=0.5',
                      'zope.sqlalchemy',
                      'zope.component',
                      'zope.event',
                      'zope.schema',
                      ],
    packages=find_packages(exclude=["*.tests"]),
    namespace_packages=['ore'],
    package_data = {
      '': ['*.txt', '*.zcml', '*.pt'],
    },
    zip_safe=False,
    author='Kapil Thangavelu',
    author_email='kapil.foss@gmail.com',
    description="Deploy/Rescue Content from Plone to a Relational Database",
    long_description=read("ore","contentmirror","readme.txt"),
    license='GPL',
    keywords="plone zope zope3",
    entry_points={
     'console_scripts': ['mirror-ddl = ore.contentmirror.ddl:main',
                         'mirror-bulk = ore.contentmirror.batch:main'],
        }
    )
