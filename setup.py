from distutils.core import setup

setup(
    name='scale',
    version='0.1.0',
    packages=['scale', 'tests', 'tests.steps'],
    url='',
    license='MIT',
    author='Christopher S. Case',
    author_email='chris.case@g33xnexus.com',
    description='An asynchronous application framework for python, based off node.js',
    requires=['pyuv']
)
