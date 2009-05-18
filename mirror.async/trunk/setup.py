import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name="mirror.async",
    version=read('version.txt').strip(),
    url="http://contentmirror.googlecode.com",
    install_requires=[
        'setuptools',
        'amqplib',
        'boto',
        'zope.component',
        'ore.contentmirror'
        ],
    packages=find_packages(exclude=["*.tests"]),
    namespace_packages=['mirror'],
    package_data = {
      '': ['*.txt', '*.zcml', '*.pt'],
    },
    zip_safe=False,
    author='Kapil Thangavelu',
    author_email='kapil.foss@gmail.com',
    description="Content Mirror Async Operations",
    long_description=read('mirror', 'async', 'readme.txt'),
    license='GPL',
    keywords="zope plone"
    )
