from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys

def read_file(path):
    with open(path) as f:
        return f.read()

readme = read_file('README.rst')
_, rest = readme.split('.. pypi-start')
text, _ = rest.split('.. pypi-end')
long_description = text.replace('`', '').replace('**', '').replace('::', '')

class Unsupported(TestCommand):
    def run(self):
        print("Running 'test' with setup.py is not supported. "
              "Use 'pytest' or 'tox' to run the tests.")

PACKAGES = find_packages(where='.', exclude=['timeboard.tests'])

setup(name='timeboard',
      version=read_file('timeboard/VERSION.txt').strip(),
      description='Calendar calculations over business days and work shifts',
      long_description=long_description,
      classifiers=[
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.6',
          'Topic :: Office/Business :: Scheduling',
      ],
      keywords='business day calendar schedule calculation shift',
      url='http://timeboard.readthedocs.io',
      author='Maxim Mamaev',
      author_email='mmamaev2@gmail.com',
      license='BSD 3-Clause',
      packages=PACKAGES,
      include_package_data=True,
      install_requires=read_file('requirements.txt').strip().split('\n'),
      test_suite='timeboard.tests',
      cmdclass={
          "test": Unsupported
      },
      zip_safe=False)
