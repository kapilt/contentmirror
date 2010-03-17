import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name="mirror.pfg",
    version=read('version.txt').strip(),
    url="http://contentmirror.googlecode.com",
    install_requires=['setuptools',
                      'zope.testing',
                      'ore.contentmirror'],
    packages=find_packages(exclude=["*.tests"]),
    namespace_packages=['mirror'],
    package_data = {
      '': ['*.txt', '*.zcml'],
    },
    zip_safe=False,
    author='Tim Knapp',
    description="Extension for Content Mirror to Support Plone Form Gen",
    license='GPL',
    keywords="plone",
    )
