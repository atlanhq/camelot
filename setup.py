import os
from setuptools import find_packages
from pkg_resources import parse_version


here = os.path.abspath(os.path.dirname(__file__))
about = {}
with open(os.path.join(here, 'camelot', '__version__.py'), 'r') as f:
    exec(f.read(), about)

# TODO: Move these to __version__.py
NAME = 'camelot-py'
VERSION = about['__version__']
DESCRIPTION = 'PDF Table Parsing for Humans'
with open('README.md') as f:
    LONG_DESCRIPTION = f.read()
URL = 'https://github.com/socialcopsdev/camelot'
AUTHOR = 'Vinayak Mehta'
AUTHOR_EMAIL = 'vmehta94@gmail.com'
LICENSE = 'MIT License'


def setup_package():
    reqs = []
    with open('requirements.txt', 'r') as f:
        for line in f:
            reqs.append(line.strip())

    dev_reqs = []
    with open('requirements-dev.txt', 'r') as f:
        for line in f:
            dev_reqs.append(line.strip())

    metadata = dict(name=NAME,
                    version=VERSION,
                    description=DESCRIPTION,
                    long_description=LONG_DESCRIPTION,
                    url=URL,
                    author=AUTHOR,
                    author_email=AUTHOR_EMAIL,
                    license=LICENSE,
                    packages=find_packages(exclude=('tests',)),
                    install_requires=reqs,
                    extras_require={
                        'dev': dev_reqs
                    },
                    entry_points={
                        'console_scripts': [
                            'camelot = camelot.cli:cli',
                        ],
                    },
                    classifiers=[
                        # Trove classifiers
                        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
                        'License :: OSI Approved :: MIT License',
                        'Programming Language :: Python :: 2.7'
                    ])

    try:
        from setuptools import setup
    except:
        from distutils.core import setup

    setup(**metadata)


if __name__ == '__main__':
    setup_package()