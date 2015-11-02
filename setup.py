from setuptools import setup, find_packages
import sys

sys.path.append("./pyzxcvbn")
sys.path.append('./tests.py')

setup(
    name='pyzxcvbn',
    version='0.5',
    description="Python version zxcvbn",
    packages=find_packages(),
    test_suite='tests.suite'
)
