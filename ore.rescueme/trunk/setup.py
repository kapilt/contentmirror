import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name="ore.rescueme",
    version="0.3.4",
    # play the standard zope2 game to lie about our dependencies...
    # actual would include 'zope.event', 'zope.schema', 'zope.component'
    # plus 'zope.app.container', this last one ends up pulling most of
    # zope3.
    install_requires=['setuptools', 'ore.alchemist', 'zope.app.container'],

    packages=find_packages(exclude=["*.tests"]),
    namespace_packages=['ore'],
    package_data = {
      '': ['*.txt', '*.zcml', '*.pt'],
    },
    zip_safe=False,
    author='Kapil Thangavelu',
    author_email='kapil.foss@gmail.com',
    description="Deploy/Rescue Content from Plone to a Relational Database",
    long_description=read("ore","rescueme","readme.txt"),
    license='GPL',
    keywords="plone zope zope3",
    entry_points={
     'console_scripts': ['mirror-ddl = ore.rescueme.ddl:main'],
    }
    )
