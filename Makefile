PYTHON ?= python
NOSETESTS ?= nosetests

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