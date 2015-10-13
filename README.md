This is the Python reference implementation for GUANO, the "Grand Unified
Acoustic Notation Ontology", a metadata format for bat acoustics recordings.

It includes a simple Python module with support for reading and writing
GUANO metadata.

The actual preliminary GUANO specification can be found at 
[doc/guano_specification.md](doc/guano_specification.md).


Requirements
============

- Python 2.7


Installation
============

Download and install magically from the Python Package Index::

    $> pip install -U guano


Check out the project from GitHub and install locally in developer mode to hack on it yourself::

    $> git clone https://github.com/riggsd/guano-py.git
    $> cd guano-py
    $> python setup.py develop


Usage
=====

```python
from guano import GuanoFile

f = GuanoFile('test.wav')

print f['GUANO|Version']
>>> 1.0

print f['Make'], f['Model']
>>> 'Pettersson', 'D500X'

print f['PET', 'GAIN']
>>> 80

f['Species Manual ID'] = 'Myso'

f['Note'] = 'I love GUANO!'

f.write()
```
