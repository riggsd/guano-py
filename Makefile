PYTHON=python2


clean:
	rm -rf *.pyo *.pyc *.egg-info dist

test:
	$(PYTHON) -m unittest discover -s tests

dist:
	$(PYTHON) setup.py sdist bdist_wheel

upload: dist
	twine upload dist/*.*
