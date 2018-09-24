# -*- coding: utf-8 -*-

import os
from setuptools import find_packages
from pkg_resources import parse_version


here = os.path.abspath(os.path.dirname(__file__))
about = {}
with open(os.path.join(here, 'camelot', '__version__.py'), 'r') as f:
    exec(f.read(), about)

with open('README.md', 'r') as f:
    readme = f.read()


def setup_package():
    reqs = []
    with open('requirements.txt', 'r') as f:
        for line in f:
            reqs.append(line.strip())

    dev_reqs = []
    with open('requirements-dev.txt', 'r') as f:
        for line in f:
            dev_reqs.append(line.strip())

    metadata = dict(name=about['__title__'],
                    version=about['__version__'],
                    description=about['__description__'],
                    long_description=readme,
                    long_description_content_type="text/markdown",
                    url=about['__url__'],
                    author=about['__author__'],
                    author_email=about['__author_email__'],
                    license=about['__license__'],
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