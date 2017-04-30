Example API Use
===============

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
