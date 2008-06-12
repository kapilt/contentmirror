from setuptools import setup, find_packages

setup(
    name="ore.rescueme",
    version="0.3.2",
    install_requires=['setuptools',
                      'zope.schema',
                      'zope.app.container',
                      'ore.alchemist'],

    packages=find_packages(exclude=["*.tests"]),
    namespace_packages=['ore'],
    package_data = {
      '': ['*.txt', '*.zcml', '*.pt'],
    },
    zip_safe=False,
    author='Kapil Thangavelu',
    author_email='kapil.foss@gmail.com',
    description="Deploy/Rescue Content from Plone to a Relational Database",
    license='GPL',
    keywords="plone zope zope3",
    )
