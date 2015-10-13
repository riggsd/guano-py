This is the Python reference implementation for the GUANO Metadata project.


Requirements
============

- Python 2.6 or 2.7


Usage
=====

from guano import GuanoFile

f = GuanoFile('test.wav')

print f['Make'], f['Model']
>> 'Pettersson', 'D500X'

print f['PET', 'GAIN']
>> 80
