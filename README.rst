guano-py
========

This is the `Python`_ reference implementation for `GUANO`_, the “Grand
Unified Acoustic Notation Ontology”, a metadata format for bat acoustics
recordings. It includes a production-ready Python module with full
support for reading and writing GUANO metadata, as well as several
helpful commandline utilities.

For more information about GUANO metadata itself, including the format
specification, see the GUANO project homepage: http://guano-md.org

Documentation for guano-py can be found at: http://guano-py.readthedocs.io


Requirements
============

-  Python 2.7 or Python 3.3+


Installation
============

Download and install magically from the Python Package Index::

    $> pip install -U guano

In addition to having the ``guano`` Python module available for use in
your own software, you’ll also have a small collection of `useful
scripts`_ to use.

Alternately, you can check out the project from GitHub and install
locally in developer mode to hack on it yourself::

    $> git clone https://github.com/riggsd/guano-py.git
    $> cd guano-py
    $> python setup.py develop

|Build Status| |Documentation Status|


API Usage
=========

.. code:: python

    from guano import GuanoFile

    # load a .WAV file with (or without) GUANO metadata
    g = GuanoFile('test.wav')

    # get and set metadata values like a Python dict
    print g['GUANO|Version']
    >>> 1.0

    print g['Make'], g['Model']
    >>> 'Pettersson', 'D500X'

    g['Species Manual ID'] = 'Myso'

    g['Note'] = 'I love GUANO!'

    # namespaced fields can be specified separately or pipe-delimited
    print g['PET', 'Gain'], g['PET|Gain']
    >>> 80, 80

    g['SB|Consensus'] = 'Epfu'
    g['SB', 'Consensus'] = 'Epfu'

    # print all the metadata values
    for key, value in g.items():
        print '%s: %s' % (key, value)

    # write the updated .WAV file back to disk
    g.write()

    # have some GUANO metadata from some other source? load it from a string
    g = GuanoFile.from_string('GUANO|Version:1.0\nTags:voucher,hand-release')

    # write GUANO metadata somewhere else, say an Anabat file or text file
    with open('sidecar_file.guano', 'wb') as outfile:
        outfile.write( g.serialize() )

    # teach the parser to recognize custom metadata fields
    GuanoFile.register('Anabat', ['Humidity', 'Temperature'], float)
    GuanoFile.register('SB', 'Thumbnail Image', guano.base64decode)


.. _Python: http://python.org
.. _GUANO: http://guano-md.org
.. _useful scripts: bin/

.. |Build Status| image:: https://travis-ci.org/riggsd/guano-py.svg?branch=master
   :target: https://travis-ci.org/riggsd/guano-py
.. |Documentation Status| image:: https://readthedocs.org/projects/guano-py/badge/?version=latest
   :target: http://guano-py.readthedocs.io/en/latest/?badge=latest
