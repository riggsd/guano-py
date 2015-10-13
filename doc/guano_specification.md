GUANO - Grand Unified Acoustic Notation Ontology
================================================

This document outlines an extensible metadata format specifically for use with
bat acoustic recordings, GUANO, the "Grand Unified Acoustic Notation Ontology".


Project Goals
-------------

Among current manufacturers of bat detectors, and even among models of bat
detectors from the same manufacturer, there exists wildly incompatible
formats for persisting metadata about echolocation recordings. This severely
impacts interoperability during post-processing and analysis.

GUANO aims to provide an open and extensible format which any manufacturer
of hardware or software may utilize for persisting metadata, such that their
metadata may be semantically interpreted. 

This format specifically deals with embedding metadata into .WAV (RIFF) files,
as the current bulk of incompatible industry formats pertains to direct or
time-expanded full-spectrum recordings in the .WAV format. Other file formats
are in use (examples include WavPack recordings from Binary Acoustic Technology
hardware, and WAC recordings from Wildlife Acoustics hardware), and
manufacturers are invited to explore the application of GUANO metadata to those
file formats; but this specification concentrates only on the standard .WAV.


Status
------

This format and specification are in the early pre-implementation stage. No
bat detector manufacturer currently writes GUANO metadata; and with the
exception of this reference implementation, no software ecosystem currently
supports reading or editing GUANO metadata.

GUANO will be considered at the "Version 1.0" stage when the first conforming
implementation hardware is released publically.


Definitions and Common Data Conventions
---------------------------------------

All GUANO metadata must be persisted in big-endian format; multi-byte values
are to be written such that the most significant byte has the lowest address
and the least significant byte has the highest address. This is because files
are written once, but read many times; by standardizing on an endianness we
ease the burden on subsequent processing and analysis, regardless of hardware
platform used for recording. This has no bearing on whether recorders choose
to write little- or big-endian .WAV data, as specified in the .WAV (RIFF) file
header; the GUANO metadata itself must be written big-endian.

All GUANO metadata must be persisted as UTF-8 Unicode string. This is a multi-
byte encoding which uses just a single byte for all "ASCII" data, but a
variable number of bytes for encoding "special" characters. 

That's right, all data must be written as UTF-8 string. GUANO does not allow
a binary representation for floating point data (eg. IEEE 754), but rather
requires the base10 string literal representation.

Newlines must be specified with the '\n' linefeed (UTF-8 and ASCII 0x0A)
character only.

Values which need to encode a literal newline should write the two-byte string
"\n" (UTF-8 and ASCII 0x5C, 0x6E). Correspondingly, software which reads
fields that support multi-line string values should interpret the literal
string "\n" as a newline. At this time, this specification makes no attempt
to define an escape for encoding the literal string "\n" with a meaning apart
from "newline".

Extra whitespace may be used when formatting field names and values; whitespace
should be trimmed upon reading. This gives writing implementations freedom to
optionally format the metadata upon writing for clarity or organization. This
also allows writing implementations to initialize a fixed-size block containing
only whitespace characters (eg. UTF-8 and ASCII space character 0x20) for
performance, then write specific metadata values after actual recording data
has been streamed to disk. Because .WAV sample data must be aligned to even
byte boundaries, implementations should pad the GUANO metadata sub-chunk with
whitespace to an even number of bytes.

Reading implementations should ignore all metadata fields which they do not
recognize (for example, new fields from later metadata specification versions,
or namespaced manufacturer-specific fields). Editing implementations should
persist all unknown metadata fields exactly as read.

Dates, times, and datetimes must appear in one of the following formats, which
are subsets of the ISO 8601 and RFC 3331 specifications.

**Date**

* 2015-12-31

**Time**

* 23:59
* 23:59:59
* 23:59:59.123
* 23:59:59.123456

**Local DateTime**

* 2015-12-31T23:59:59
* 2015-12-31T23:59:59.123
* 2015-12-31T23:59:59.123456

**UTC DateTime**

* 2015-12-31T23:59:59Z
* 2015-12-31T23:59:59.123Z
* 2015-12-31T23:59:59.123456Z

**UTC Relative DateTime***

* 2015-12-31T23:59:59+04:00
* 2015-12-31T23:59:59.123+04:00
* 2015-12-31T23:59:59.123456+04:00


Embedding in WAVE Files
-----------------------

The canonical .WAV file consists of a ``fmt_`` sub-chunk, which provides metadata
about the recording data itself, and a ``data`` sub-chunk, which contains that
primary recording data.

GUANO metadata, when embedded in a .WAV file, must be placed into its own
sub-chunk with ID ``guan``. Implementations are free to locate the ``guan`` sub-chunk
anywhere within the RIFF container they wish. Writing implementations may prefer
to place this sub-chunk at the end of the .WAV file (so they can efficiently
stream recording data to disk with minimal buffering), while reading
implementations may wish it were located at the start (so they don't need to
read the entire file into memory). This means that all implementations must
conform to the RIFF format and jump sub-chunk to sub-chunk if necessary.


Metadata Format
---------------

Namespaces are separated from field keys by the first occurrence of the '|'
pipe character, UTF-8 and ASCII ``0x7C``. Namespaces may not include a '|'
character (obviously) or a ':' character.

Field keys are separated from field values by the first occurrence of the ':'
colon character, UTF-8 and ASCII ``0x3A``. Keys may not contain a ':'
character (obviously). Keys may contain a '|' character so that vendors may
namespace their own vendor-specific fields; for example,
`PET|D500X|TSens: high` could be a value which applies to Pettersson's D500X
but not to their other products.

Field values consist of everything after the first ':' character, until the
next '\n' newline (or EOF), and after having all surrounding whitespace
trimmed. Whitespace is not exhaustively defined here, but should include the
non-printing ASCII bytes including null, CR, LF, space, tab, etc.

Empty lines are ignored. In fact, the examples in this document use extra
empty lines for legibility, though this is absolutely not a requirement for
writing implementations.

Field keys may occur in any order. However, keys may not be duplicated within
a single file!


Extensible Namespaces
---------------------

Manufacturers are encouraged to include metadata specific to their own hardware
or software. The GUANO specification provides a catalog of common fields, but
allows for the inclusion of custom fields.

Custom field names must be namespaced with an identifier. Identifiers should be
registered in this document so that they are not inadvertently reused, but
manufacturers are free to use as many or as few custom fields as they like
(it's your namespace!).


### Reserved Namespaces ###

The following namespaces have been reserved or registered. Any manufacturer who
utilizes their own custom GUANO fields is encouraged to add their namespace to
this list so that it isn't accidentally used by another manufacturer.

**GUANO**
  This reserved namespace is for meta-metadata pertaining specifically to the
  GUANO metadata in use.

**BAT**
  Binary Acoustic Technologies

**MSFT**
  Myotisoft

**PET**
  Pettersson

**SB**
  SonoBat

**Anabat**
  Titley Scientific

**WAC**
  Wildlife Acoustics


Example
-------

The following example is the embedded GUANO metadata for a direct-recorded
(no time-expansion) full-spectrum recording made with a Pettersson D1000X,
then auto-classified with SonoBat, and subsequently manually vetted::

    GUANO|Version:  1.0
    
    Timestamp:  2012-03-29T03:58:01+04:00
    Species Auto ID:  MYLU
    Species Manual ID:  Myosod
    Tags:  hand-release, voucher, workshop
    Note:  Hand release of male Indiana Bat caught in triple-high net at Mammoth Cave Historic Ent.\nReleased in low-clutter 100m diameter clearing, bat flew directly overhead, circled once, then darted off into cluttered forest.\n\nRecorded by David Riggs with Pettersson D1000X at 2014 BCM acoustic workshop.
    TE:  1
    Samplerate:  500000
    Length:  6.5
    Filter HP:  20.0
    Make:  Pettersson
    Model:  D1000X
    Loc Position:  37.1878016 -86.1057312
    Loc Accuracy:  20
    Loc Elevation:  228.6
    
    SB|Version:  3.4
    SB|Classifier:  US Northeast
    SB|DiscrProb:  0.913
    SB|Filter:  20kHz Anti-Katydid
    
    PET|Gain:  80
    PET|Firmware:  1.0.4 (2009-11-25)



Defined Fields
--------------

**GUANO|Version**
  required, float. GUANO metadata version in use. This specification defines version `1.0`.

**GUANO|Size**
  optional, integer. Total size, in bytes, of pre-allocated GUANO metadata space. Pre-allocating whitespace within the `guan` subchunk allows for writing/editing metadata without re-writing the entirety of the file back to disk. This field should only be used if pre-allocating space, so that writing (editing) implementations may check to see if their changes overflow the bounds of pre-allocated metadata space.

**Filter HP**
  optional, float. High-pass filter frequency, in kHz.

**Filter LP**
  optional, float. Low-pass filter frequency, in kHz.

**Length**
  optional, float. Recording length, in seconds. This should be the "actual length", which will be identical to the .WAV length for direct-recorded files, but will be calculated for time-expanded recordings (.WAV length divided by TE factor).

**Loc Accuracy**
  optional, float. Location accuracy, in meters.

**Loc Elevation**
  optional, float. Elevation / altitude above mean sea level, in meters.

**Loc Position**
  optional, (float float). Location that the recording was made, as a WGS84 latitude longitude tuple.

**Make**
  optional, string. Manufacturer of the recording hardware.

**Model**
  optional, string. Model name or number of the recording hardware.

**Note**
  optional, multiline string. Freeform textual note associated with the recording.

**Samplerate**
  optional, integer. Recording samplerate, in Hz.

**Species Auto ID**
  optional, string. Species or guild classification, as determined by automated classification.

**Species Manual ID**
  optional, string. Species or guild classification, as determined by a human.

**Tags**
  optional, list of strings. A comma-separated list of arbitrary strings so that end users may easily apply any tags / labels that they see appropriate.

**TE**
  optional, integer. Time-expansion factor. If not specified, then 1 (no time-expansion) is assumed.

**Timestamp**
  required, datetime. Date and time of the start of the recording, in ISO 8601 format. It is very strongly recommended that, if UTC offset is known, it is explicitly specified rather than recording the timestamp only in UTC "zulu" time. This is because local time is overwhelmingly more important when it comes to bat echolocation data than is absolute UTC time; unfortunately GPS receivers provide only UTC time, and the local UTC offset for a location may vary according to political boundaries. 
