from pkg_resources import parse_version

import camelot

NAME = 'camelot'
VERSION = camelot.__version__
DESCRIPTION = 'PDF Table Parsing for Humans'
with open('README.md') as f:
    LONG_DESCRIPTION = f.read()
URL = 'https://github.com/socialcopsdev/camelot'
AUTHOR = 'Vinayak Mehta'
AUTHOR_EMAIL = 'vmehta94@gmail.com'
LICENSE = 'BSD License'

opencv_min_version = '2.4.8'


def get_opencv_status():
    """
    Returns a dictionary containing a boolean specifying whether OpenCV
    is up-to-date, along with the version string (empty string if
    not installed).
    """
    opencv_status = {}
    try:
        import cv2
        opencv_version = cv2.__version__
        opencv_status['up_to_date'] = parse_version(
            opencv_version) >= parse_version(opencv_min_version)
        opencv_status['version'] = opencv_version
    except ImportError:
        opencv_status['up_to_date'] = False
        opencv_status['version'] = ""
    return opencv_status


def setup_package():
    reqs = []
    with open('requirements.txt', 'r') as f:
        for line in f:
            reqs.append(line.strip())

    metadata = dict(name=NAME,
                    version=VERSION,
                    description=DESCRIPTION,
                    long_description=LONG_DESCRIPTION,
                    url=URL,
                    author=AUTHOR,
                    author_email=AUTHOR_EMAIL,
                    license=LICENSE,
                    packages=['camelot'],
                    install_requires=reqs,
                    entry_points={
                        'console_scripts': [
                            'camelot = camelot.cli:cli',
                        ],
                    })

    try:
        from setuptools import setup
    except:
        from distutils.core import setup

    opencv_status = get_opencv_status()
    opencv_req_str = "camelot requires OpenCV >= {0}.\n".format(opencv_min_version)

    if opencv_status['up_to_date'] is False:
        if opencv_status['version']:
            raise ImportError("Your installation of OpenCV {} is out-of-date.\n{}"
                              .format(opencv_status['version'], opencv_req_str))
        else:
            raise ImportError("OpenCV is not installed.\n{}"
                              .format(opencv_req_str))

    setup(**metadata)


if __name__ == '__main__':
    setup_package()
