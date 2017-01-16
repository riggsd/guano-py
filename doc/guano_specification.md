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

This format and specification are in the production phase. There currently exist
hardware bat detectors which write GUANO-format recordings, and real-world
software which reads and writes GUANO metadata.

GUANO is considered at the "Version 1.0" stage, and though no significant
backwards incompatible changes will be made to this 1.0 version of the format,
slight clarifications and bugfixes may be made to this specification in order
to best address vendor and user concerns. The changelog at the end of this
document details all changes to the specification going forward.

Note that mention of manufacturers and products within this specification are
used for reference or for example, and do not indicate adoption or
endorsement of the GUANO format by those manufacturers unless explicitly
stated so.


Definitions and Common Data Conventions
---------------------------------------

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

Binary field values should be encoded as Base64 strings as defined in
[RFC 4648](https://www.ietf.org/rfc/rfc4648.txt). Newlines may not be inserted
into the data, and the "Base 64 Alphabet" must be used.

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
are subsets of the [ISO 8601](https://wikipedia.org/wiki/ISO_8601) and 
[RFC 3339](https://tools.ietf.org/html/rfc3339) specifications.

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

**UTC Relative DateTime**

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
but not to their other products. Field keys are case sensitive, and whitespace
within is significant.

Field values consist of everything after the first ':' character, until the
next '\n' newline (or EOF), and after having all surrounding whitespace
trimmed. Whitespace is not exhaustively defined here, but should include the
non-printing ASCII bytes including null, CR, LF, space, tab, etc.

Empty lines are ignored. In fact, the examples in this document use extra
empty lines for legibility, though this is absolutely not a requirement for
writing implementations.

The `GUANO` namespace must occur before any others, and the `GUANO|Version`
field must be the first field in a metadata block. This is to ensure that,
if future format changes are incompatible, reading implementations may
change their behavior for older format versions. Other than the `GUANO`
namespace restriction, namespaces and field keys may occur in any order.
However, keys may not be duplicated within a single file!


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

**User**  
  Reserved namespace for user-defined fields.

**Anabat**  
  Titley Scientific

**BAT**  
  Binary Acoustic Technologies
  
**BATREC**  
  Bat Recorder by Bill Kraus

**MSFT**  
  Myotisoft

**PET**  
  Pettersson

**SB**  
  SonoBat

**WA**  
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

Writing implementations, whenever possible, are encouraged to utilize
fields from the following defined or "well-known" list. 

Reading implementations should expect to encounter any of the following
fields in a compliant GUANO file. 

**GUANO|Version**  
  required, string. GUANO metadata version in use. Not only is this field required, but it *must* be the first field that appears within a GUANO metadata subchunk. Its value is a string, which may be compared lexicographically, and which defines the GUANO specification version that the file conforms to. This specification defines version `1.0`.

**Filter HP**  
  optional, float. High-pass filter frequency, in kHz.

**Filter LP**  
  optional, float. Low-pass filter frequency, in kHz.

**Firmware Version**  
  optional, string. Device's firmware version, in manufacturer's own descriptive format.

**Hardware Version**  
  optional, string. Device's hardware revision or hardware options, in manufacturer's own descriptive format.

**Humidity**  
  optional, float. Relative humidity as a percentage in the range 0.0 - 100.0.

**Length**  
  optional, float. Recording length, in seconds. This should be the "actual length", which will be identical to the .WAV length for direct-recorded files, but will be calculated for time-expanded recordings (.WAV length divided by TE factor).

**Loc Accuracy**  
  optional, float. Location accuracy, in meters. This should be the Estimated Position Error (EPE); this statistical range states that 68% of measurements will fall within this radius, 95% of measurements will fall within twice this radius. EPE is calculated differently by different GPS receiver manufacturers, therefore it should be stressed that this value is merely an *estimate* of accuracy. Detector manufacturers may opt to estimate accuracy more coarsely if EPE is not available directly from their GPS receiver, but should express the value in the same one-sigma fashion.

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

**Original Filename**  
  optional, string. The original filename as used by the recording hardware. Editing implementations should persist this value after renaming and/or editing a file as a sort of "paper trail".

**Samplerate**  
  optional, integer. Recording samplerate, in Hz. This should be equal to the .WAV samplerate for direct-recording detectors, but should be a product of ``TE`` and the .WAV samplerate for time-expansion detectors.

**Serial**  
  optional, string. Serial number or unique identifier of the recording hardware.

**Species Auto ID**  
  optional, list of strings. Species or guild classifications, as determined by automated classification. This field allows a comma-separated list of values, however some reading implementations may only be able to handle a single species per file; therefore the most "dominant" or "primary" species present in a file, when applicable, should be the first value in this list.

**Species Manual ID**  
  optional, list of strings. Species or guild classifications, as determined by a human.  This field allows a comma-separated list of values, however some reading implementations may only be able to handle a single species per file; therefore the most "dominant" or "primary" species present in a file, when applicable, should be the first value in this list.

**Tags**  
  optional, list of strings. A comma-separated list of arbitrary strings so that end users may easily apply any tags / labels that they see appropriate.

**TE**  
  optional, integer. Time-expansion factor. If not specified, then 1 (*no* time-expansion, aka direct-recording) is assumed.

**Temperature Ext**  
  optional, float. External temperature in degrees Celsius. This is the temperature outside the device's housing - the "ambient" temperature.

**Temperature Int**  
  optional, float. Internal temperature in degrees Celsius. This is the temperature as measured inside the device's housing, where there is an expectation of some variance from actual "ambient" temperature.

**Timestamp**  
  required, datetime. Date and time of the start of the recording, in ISO 8601 compatible format (see datetime specification above). It is very strongly recommended that, if UTC offset is known, it is explicitly specified rather than recording the timestamp only in UTC "zulu" time. This is because local time is overwhelmingly more important when it comes to bat echolocation data than is absolute UTC time; unfortunately GPS receivers provide only UTC time, and the local UTC offset for a location may vary according to political boundaries. 


Specification History
---------------------

2017-01-15 | 1.0.0 | Updated GUANO specification status to reflect production nature of format.
                     Allow multiple values for `Species Auto ID` and `Species Manual ID`.
                     Added `Serial` and `Original Filename` fields.
                     Removed redundant `GUANO|Size` field.
                     Re-added `WA` vendor namespace for Wildlife Acoustics.

2016-05-15 | 0.0.4 | Added `BATREC` vendor namespace for Android Bat Recorder by Bill Kraus. 
                     Separated `Temperature` field into `Temperature Ext` and `Temperature Int`.

2016-03-02 | 0.0.3 | Clarified Base64 encoding of binary data. Added `User` namespace. Removed
                     mention of UTF-8 endianness.

2016-01-30 | 0.0.2 | Added well-known fields: `Hardware Version`, `Firmware Version`, `Temperature`, `Humidity`.  
                     Clarified `Loc Position` description.

2015-10-12 | 0.0.1 | Initial public release of draft GUANO specification with reference Python implementation

2014-10-03 | 0.0.0 | Initial private draft of GUANO metadata specification.


Notes
-----

* The use of manufacturer or product names in this specification does not imply endorsement,
  support, or any other association by those manufacturers or products; nor does it imply compliance
  with the GUANO specification.
