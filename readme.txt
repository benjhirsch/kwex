Using kwex
==========

This tool takes as input a CSV file containing a list of keywords and a FITS
file from which you wish to extract those keywords and their values. It outputs
a text file (extension ".kwl") with a form similar enough to a PDS3 label file
that the MILabel tool can read it and populate a Velocity template.

kwex is a Python script run by the Python interpreter and therefore requires
Python (3.x) to use. Make sure to place the tool somewhere in your Python PATH.

The basic command for running the script is:

python kwex.py -f <path to fits file> -k <path to csv file>

With this command, it will read the FITS file along with any PDS3 label that has
the same name (and a .lbl extension) and output a .kwl file of the same name in
the directory of the FITS file.


Optional Parameters
===================

-l <path to lbl file>       Specifies a different name for the PDS3 label file.

-o <path to output file>    Specifies a different name for the output file.

-d <optional log file>      Prints some minimal debugging to the console.
							
-h, --help                  Print this file to the console.


CSV Input File
==============

This file contains the keywords you want to extract. Entries in the file take
the form:

KEYWORD,SOURCE

where source specifies where kwex is getting the keyword from. Currently valid
sources are "FITS", "PDS3", and "COMMENT". COMMENT refers to comments in the
PDS3 label, which for annoying reasons the tool has to process a bit
differently.


Reading FITS Keywords
=====================

By default, kwex searches for keywords in the primary header. To specify a
different header, write the keyword as:

KEYWORD_EXTN,FITS

where N is the number of the extension. 0 is the primary header, so you probably
want to begin with 1 for the first extension.

If you need to read keywords that can be enumerated a variable number of times
within a FITS header, the format is:

KEYWORD.LOOP,FITS

This will extract values from every instance of KEYWORDNN, where NN is the index
of the keyword. It will appear in the output file as a "LOOP" object. Currently,
kwex can only look for iterative keywords in the primary header.


Reading PDS3 Keywords
=====================

This is mostly unproblematic. To read from a keyword within a PDS3 nested
object, write:

OBJECT_N_KEYWORD,PDS3

"OBJECT" is whatever is at the end of the "OBJECT = " line of the object you're
looking for, N is the nth instance of that object (0-indexed), and KEYWORD is
the keyword inside that object.

To pull a keyword from inside a comment in a PDS3 label, write:

KEYWORD,COMMENT

This is still looking for a keyword = value pair in the PDS3 label, but has some
flexibility about where it finds it because of the nature of comment/note
fields. That flexibility also means it might screw up sometimes and glob a
little extra.


Output KWL File
===============

The file kwex generates is designed to mirror the structure of a PDS3 label so
that MILabel can read it. In general, each line will appear as:

KEYWORD = VALUE

where keyword and value will be exactly the same as they were in whatever file
you got them from. Exceptions include floats with trailing 0s after the decimal
point in FITS headers, because astropy does not by default respect the native
precision. To reference a keyword value pair in a .vm template, write:

$label.KEYWORD

where KEYWORD appears exactly as it does in the .kwl file.

Additionally, any iterative keywords from the FITS header will be placed into a
repeating, PDS3-like object like this:

OBJECT = LOOP
KEYWORD = VALUE
KEYWORD = VALUE
END_OBJECT = LOOP
OBJECT = LOOP
KEYWORD = VALUE
KEYWORD = VALUE
END_OBJECT = LOOP

This object structure will be repeated for every instance of the keyword in
question. Any NN index that was at the end of the keyword in the FITS header
will NOT be here, because the index is instead encoded in which LOOP object
MILabel finds the keyword in. To reference a particular keyword within an object
in your .vm file, write:

$label.LOOP.get(N).KEYWORD

where N is the nth instance of LOOP (0-indexed). It's more likely, however, that
you'll want a #foreach structure in your template that takes every instance of
the keyword, so in the template it will probably look something like:

$label.LOOP.get($foreach.index).KEYWORD


Contact Info
============

For any questions or issues, contact Ben Hirsch of the PDS Small Bodies Node at
bhirsch1@umd.edu.
