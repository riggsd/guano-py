PYTHON=python

.PHONY: help clean test docs dist upload

help:
	@echo
	@echo make targets for guano-py
	@echo
	@echo help ..... Print this helpful documentation
	@echo clean .... Clean up build artifacts
	@echo test ..... Run all project unit tests
	@echo docs ..... Build documentation
	@echo dist ..... Build distributable package
	@echo upload ... Build and upload distributable package to PyPI
	@echo
	@echo specify an explicit Python version like this:
	@echo "    $$> make test PYTHON=python3"
	@echo

clean:
	rm -rf *.pyo *.pyc *.egg-info bin/*.pyc dist __pycache__

test:
	$(PYTHON) -m unittest discover -s tests

docs:
	cd docs && make html

dist:
	$(PYTHON) setup.py sdist bdist_wheel --universal

upload: dist
	twine upload dist/*.*
