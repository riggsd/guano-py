Changelog
=========


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
