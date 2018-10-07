# -*- coding: utf-8 -*-

import os
from setuptools import find_packages


here = os.path.abspath(os.path.dirname(__file__))
about = {}
with open(os.path.join(here, 'camelot', '__version__.py'), 'r') as f:
    exec(f.read(), about)

with open('README.md', 'r') as f:
    readme = f.read()


requires = [
    'click==6.7',
    'matplotlib==2.2.3',
    'numpy==1.15.2',
    'openpyxl==2.5.8',
    'pandas==0.23.4',
    'pdfminer.six==20170720',
    'PyPDF2==1.26.0'
]

all_requires = [
    'opencv-python==3.4.2.17'
]

dev_requires = [
    'codecov==2.0.15',
    'pytest==3.8.0',
    'pytest-cov==2.6.0',
    'pytest-runner==4.2',
    'Sphinx==1.7.9'
]
dev_requires = dev_requires + all_requires


def setup_package():
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
                    install_requires=requires,
                    extras_require={
                        'all': all_requires,
                        'dev': dev_requires
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
                        'Programming Language :: Python :: 2.7',
                        'Programming Language :: Python :: 3.5',
                        'Programming Language :: Python :: 3.6',
                        'Programming Language :: Python :: 3.7'
                    ])

    try:
        from setuptools import setup
    except ImportError:
        from distutils.core import setup

    setup(**metadata)


if __name__ == '__main__':
    setup_package()
