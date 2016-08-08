PYTHON ?= python
NOSETESTS ?= nosetests

help:
    @echo "Please use \`make <target>' where <target> is one of"
    @echo "  clean"
    @echo "  dev            to install in develop mode"
    @echo "  undev          to uninstall develop mode"
    @echo "  install        to install for all users"
    @echo "  test           to run tests"
    @echo "  test-coverage  to run tests with coverage report"

clean:
    $(PYTHON) setup.py clean
    rm -rf dist

dev:
    $(PYTHON) setup.py develop

undev:
    $(PYTHON) setup.py develop --uninstall

install:
    $(PYTHON) setup.py install

test:
    $(NOSETESTS) -s -v

test-coverage:
    rm -rf coverage .coverage
    $(NOSETESTS) -s -v --with-coverage
