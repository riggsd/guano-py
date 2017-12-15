Changelog
=========

0.0.11
------

*2017-12-14*

- Huge improvement in read speed and memory usage by lazily-loading `GuanoFile.wav_data` and by
  *not* using mmap for file access
- Add support for deleting fields as `del gfile['Species Manual ID']`
- `disperse.py`: add `--copy` option to copy rather than move files


0.0.10
------

*2017-09-30*

- Add `guano_edit.py` util for adding and changing files' GUANO metadata
- Add strict/lenient parsing option to `GuanoFile` constructor
- Use Python's `logging` framework


0.0.9
-----

*2017-07-07*

- Treat the `GUANO|Version` value as a string rather than numeric value


0.0.8
-----

*2017-05-19*

- Try to recover metadata which is incorrectly encoded (UTF-8 is required, we try to fall back to latin-1)


0.0.7
-----

*2017-04-29*

- Python 3 support
- User manual


0.0.6
-----

*2017-04-27*

- Critical bugfix for parsing some UTF-8 text
- Additional resilience when parsing bad or non-conforming GUANO metadata
- Seamlessly escape/unescape multiline string `Note` field
- Addition of `batlogger2guano.py` utility script for converting Elekon Batlogger files to use GUANO instead


0.0.5
-----

*2017-03-18*

- Add `GuanoFile()` constructor without filename for creating metadata instance which isn't tied to an underlying .WAV file
