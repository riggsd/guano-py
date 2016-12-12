PYTHON=python2


clean:
	rm -rf *.pyo *.pyc *.egg-info dist

dist:
	$(PYTHON) setup.py sdist bdist_wheel

upload: dist
	twine upload dist/*.*
