from setuptools import setup

import os, sys, re

os.environ['COPYFILE_DISABLE'] = 'true'  # this disables including resource forks in tar files on os x


extra = {}
if sys.version_info >= (3,0):
    extra['use_2to3'] = True


def long_description():
    return open('README.rst').read() + '\n' + open('CHANGELOG.txt').read()


setup(
    name="jsmin",
    version=re.search(r'__version__ = ["\']([^"\']+)', open('jsmin/__init__.py').read()).group(1),
    packages=['jsmin'],
    description='JavaScript minifier.',
    long_description=long_description(),
    author='Dave St.Germain',
    author_email='dave@st.germa.in',
    maintainer='Tikitu de Jager',
    maintainer_email='tikitu+jsmin@logophile.org',
    test_suite='jsmin.test',
    license='MIT License',
    url='https://github.com/tikitu/jsmin/',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Pre-processors',
        'Topic :: Text Processing :: Filters',
    ],
    **extra
)
