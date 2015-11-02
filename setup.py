from setuptools import setup, find_packages
import sys

import pyzxcvbn

sys.path.append("./pyzxcvbn")
sys.path.append('./tests.py')

setup(
    name=pyzxcvbn.__title__,
    packages=find_packages(),
    version=pyzxcvbn.__version__,
    author=pyzxcvbn.__author__,
    author_email=pyzxcvbn.__author_email__,
    short_description="Python version zxcvbn",
    long_description="""\
=================
pyzxcvbn
=================

Python version `zxcvbn <https://github.com/dropbox/zxcvbn>`_.
There are the same test scripts (but written in not coffee script but python) as the original repository in order to ensure this library will move in the same way.

Install
-------
::
    $ pip install pyzxcvbn

""",
    url=pyzxcvbn.__url__,
    license=pyzxcvbn.__license__,
    classmethod=[
        'License :: OSI Approved :: MIT License',
        "Programming Language :: Python",
    ],
    test_suite='tests.suite'
)
