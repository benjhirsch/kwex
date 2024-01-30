kwex 2.0 (aka kwex2xml)

Using kwex
==========

This tool takes as input a Velocity template file containing pointers to
keywords and a FITS file from which you wish to extract the values of those
keywords. It outputs the template file merged with those values.

kwex is a Python script run by the Python interpreter and therefore requires
Python (3.x) to use. Make sure to place the tool somewhere in your Python
PATH. Depending on your use case, astropy, spiceypy, and simpleeval are also
required modules; run pip install requirements.txt to install (or equivalent
for your Python environment).

kwex also uses the Java-based Apache Velocity template engine. All necessary
.jar files are included in the java/ directory, but you will need some version
of Java installed.

The basic command for running the script is:

python kwex.py -v <path to velocity template> -f <paths to fits file>

With this command, it will read the FITS file along with any PDS3 label that has
the same name (and a .lbl extension) and output a .xml file of the same name in
the directory of the FITS file.


Optional Parameters
===================

-l <path to lbl file>       Specifies a different name for the PDS3 label file.

-o <path to output file>    Specifies a different name for the output file.

-x output extension         Specifies the output file extension (when not
                            provided by -o). Default is xml.

-d                          Prints some minimal debugging to the console.

-j                          Include to not delete vals.json file at end of
                            program.

-k <path to meta kernel>    Include to calculate SPICE keywords.

-c <path to spicecalc file> Specifies a different spice calculations file.

-r <reference frame>        Specifies a different reference frame for SPICE.
                            Default is J2000.
							
-s <spacecraft>             Specifies a different spacecraft for SPICE.
                            Default is NH (NEW HORIZONS).
							
-h, --help                  Prints usage and optional parameters.


You can use wildcards (*) in the FITS file path to run kwex on multiple files
at once and produce an output PDS4 label for each one.


Velocity Template File
======================

Understanding Velocity is beyond the scope of this readme, but a guide to the
version used in this tool can be found here:

https://velocity.apache.org/engine/1.7/user-guide.html

A few basics are necessary, however. The .vm template file acts as an input
file to kwex, telling it which keywords it needs values for. At present, kwex
has 3 possible sources for keyword values: FITS files, PDS3 label files, and
SPICE function calls. A pointer to a keyword in the template file takes the
form:

$source.KEYWORD

where source is one of "fits," "label," or "spice," and keyword is (usually)
exactly as it appears in the source.


FITS Keywords
=============

By default, kwex searches for keywords in the primary header. To specify a
different header, write the pointer as:

$fits_extN.keyword

where N is the number of the extension. 0 is the primary header, so you probably
want to begin with 1 for the first extension.

If you need to read iterating keywords that repeat with a different index value
throughout the header, set keyword equal to the value of the keyword without an
index. The pointer will contain an array of all the values found which you can
loop through as needed.


PDS3 Keywords
=============

This is mostly unproblematic. To point to a keyword within a PDS3 nested
object, write:

$label.OBJECT.KEYWORD

"OBJECT" is whatever is at the end of the "OBJECT = " line of the object you're
looking for, and KEYWORD is the keyword inside that object.

If a keyword or object has multiple instances in an object/label, they will be
stored in the appropriate pointer as arrays and can be accessed like so:

$label.KEYWORD[index] (0-indexed)

For keywords with a <unit> in their value, the numeric value and unit are
accessed separately in the template file. To get the value, write:

$label.KEYWORD.value

To get the <unit>, write:

$label.KEYWORD.unit

Some PDS3 keywords are not valid variable names in Velocity/Java. To point to
these keywords in a template, a substitute variable name is required. Common
substitutes are defined in pds3/var_sub.json. More substitutes can be added
to this file. Each entry begins with a substitute string that will be used in
the template file, followed by the "pos" parameter, which indicates where the
substitute string appears in a variable name ("start", "in", or "end"), and
the "sub" parameter, which is the string in the PDS3 keyword that needs
replacing.

For example, PDS3 keywords such as "^Header" are not valid variable names in
Java due to the ^ character. The first entry in var_sub.json indicates that you
can subtitute in "PTR_" in place of ^ at the beginning of a variable name.

SPICE Keywords
==============

The "source" for SPICE keywords is the spice_calcs.json file in the spice
directory. This file contains FITS keywords and the SPICE function calls +
calculations necessary for deriving the values of those keywords. A SPICE
metakernel file (as well as all the kernels it references and the spiceypy
library) are necessary to perform these calculations. spice_calcs.json
can be updated to include more keywords/calculations, but a very limited number
of functions and variables are available for use. See names_and_functions.txt
for a list.


Java HashMaps and ArrayLists
============================

If your extracted keyword values aren't directly analogous to attributes in
your template, you can make use of the Java tools underneath the Velocity
engine. In Velocity, a hashmap can be defined like so:

#set ( $mapName = { "key1" : "value1",
                    "key2" : "value2",
                    "key3" : "value3" } )
					
and so on. These maps can even be nested for situations in which one variable
sets the value for multiple other variables. To access a map value, you can
write:

$mapName.key, $mapName[key], or $mapName.get(key)

Similarly, ArrayLists contain a list of values that can be accessed by index.
To define one, write:

#set ( $arrayName = [value1, value2, value3] )

and access them with:

$arrayName[index] (0-indexed)

These maps and arrays can be included anywhere in your template (before the
variables they define are used), or stored outside it and imported with the
following command:

#parse(filename.vm)

Again, be sure to include the parse statement before the variables it
defines are required.


Credit
======

The SPICE routines in this tool were adapted from code written by Benjamin
Sharkey, Visiting Senior Faculty Specialist at UMD, with contributions from
Adeline Gicquel-Brodtke, Senior Faculty Specialist at UMD.


Contact Info
============

For any questions or issues, contact Ben Hirsch of the PDS Small Bodies Node at
bhirsch1@umd.edu.
