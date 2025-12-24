# kwex 3
kwex (KeyWord EXtraction) is a Python tool that takes as input a Velocity template file containing pointers to keywords and one or more source (PDS3) files from which you wish to extract the values of those keywords. It outputs a PDS4 label file from the template file merged with those values.

## Usage

The basic command for running the script is:

```
kwex path/to/velocity/template path/to/source/files
```

With this command, it will read the specified source files (including any labels or data products with the same name) and output a `.lblx` file of the same name in the same location.

### Source parameter syntax options
* `path/to/source/file`
* `path/to/source/file1` `path/to/souce/file2`
* `path/to/source/directory` (does not search recursively unless that config option is enabled)
* `path/to/source/directory/*.*` (or other glob patterns)
* `@source_file_list.txt` (a file containing a list of source files)

### Optional parameters
`--output` With this argument, you can specify a different directory (or name, which is not so useful with multiple source products) for your output files.  
`--input-root` Use this argument with `--output` to capture the input directory from which to preserve the directory structure of your output.  
`--log` Include to enable logging of debug and runtime information, either to `CONSOLE` or a specified log file.  
`--override` With this argument, you can override one or more config values for this run with syntax `key=value`. See below for config options.

### Subcommands
Instead of running the primary kwex script, there are two subcommands related to configuration settings.

`kwex get_config` This command will return a list of configuration keys, their current values, and any allowed values.

`kwex set_config` `key=value` This command will store a new value for the specified configuration key in your local config file, which is used by default when running kwex.

## Configuration
kwex comes with a number of default configuration settings which can either be overriden at runtime or set in a custom local config file stored here: `~/.kwex/config/config.json`. They are:

| Key | Default | Values | Description |
|-----|---------|--------|-------------|
| logging | ENABLED | ENABLED, DISABLED | kwex can either log or not log runtime and debugging info. Critical errors are logged regardless of settings. |
| log_output | tmp/kwex.log | CONSOLE, file | By default, a log is created in the tmp directory. A setting of CONSOLE will print to the console instead. |
| warning_output | ERROR | ERROR, CONSOLE, INFO | Warnings are issued when kwex fails in some non-fatal way. By default, these messages are treated as errors and terminate the program. Instead, they can be treated identical to regular logs (INFO) or go to console but not end the program (CONSOLE). |
| output_check | DISABLED | ENABLED, DISABLED | Enable to check output files for kwex failures and log a list of those files at program end. |
| recursive_input_dir | DISABLED | ENABLED, DISABLED | Enable to search all subdirectories for --input path/to/dir. |
| find_input_pair | ENABLED | ENABLED, DISABLED | By default, kwex will search for matching labels/FITS files corresponding to the input parameter. |
| allow_unpaired | DISABLED | ENABLED, DISABLED | By default, disallow source products that consist of only one file, because this usually represents a problem. Treats as a warning if disabled. |
| keep_json | DISABLED | ENABLED, DISABLED | Keyword values are stored in a JSON file that is fed into the Velocity engine. By default, these temporary files are deleted at program end. Enable to keep them instead. |
| activate_velocity | ENABLED | ENABLED, DISABLED | By default, kwex produces output PDS4 labels with Velocity. Disable to do everything but that (if, for example, you just want the JSON keyword value files). |
| output_ext | .lblx | .* | By default, kwex produces .lblx output files. Be sure to include a period before the extension. |
| data_output | IGNORE | IGNORE, COPY, MOVE | By default, kwex does nothing with source product data files. Instead, you can COPY or MOVE them to the output location. |
| spice_kernel | n/a | *.tm | None by default. Supply whichever metakernel is needed for your data. |
| spice_equations | [spice_equations.json](src/kwex/resources/spice_equations.json) | *.json | Default file has equations for computing New Horizons SPICE geometry. |
| body_frames | [body_frames.json](src/kwex/resources/body_frames.json) | *.json | Body-fixed reference frames used by SPICE. Default list is based on New Horizons targets. |
| spice_fits_kws | [spice_fits_kws.json](src/kwex/resources/fits_spice_kws.json) | *.json | Mapping from FITS keywords to quantities needed for SPICE computations. Default list is based on New Horizons data. |
| instr_frame_params | [instr_frame_params.json](src/kwex/resources/instr_frame_params.json) | *.json | Dictionary with parameters defining instrument reference frames. Default is for New Horizons instruments. |
| spice_spacecraft | NH | [SPICE spacecraft names](https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/naif_ids.html#Spacecraft) | Default is NH. Change as necessary for mission. |
| spice_frame | J2000 | [SPICE inertial frames](https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/frames.html#Complete%20List%20of%20%60%60Built%20in''%20Inertial%20Reference%20Frames) | Default is J2000. This is mostly used as an intermediary, so unless you have quantities that need to be comptued in a different inertial frame, leave this alone. |
| abcorr | LT+S | [SPICE aberration identifiers](https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/abcorr.html#SPICE%20Aberration%20Identifiers%20also%20called%20Flags) | Default is LT+S. See SPICE documentation for details. |

## Velocity
Understanding Velocity is beyond the scope of this readme, but a guide to the version used in this tool can be found here:

https://velocity.apache.org/engine/1.7/user-guide.html

A few basics are necessary, however. The `.vm` template file acts as an input file to kwex, telling it which keywords it needs values for. At present, kwex has 3 possible sources for keyword values: FITS files, PDS3 label files, and SPICE function calls. A pointer to a keyword in the template file takes the form:

`$source.KEYWORD`

where `source` is one of `fits`, `label`, or `spice`, and `KEYWORD` is (usually) exactly as it appears in the source.

### FITS Keywords
A number of edge cases exist for FITS keywords, which are handled by adding flags to template pointer. Multiple flags can be added and order is unimportant, so long as `$fits` is first and `keyword` is last. 

By default, kwex searches for keywords in the primary header. To specify a different header, write the pointer as:

`$fits.extN.KEYWORD`

where `N` is the number of the extension. 0 is the primary header, so you probably want to begin with 1 for the first extension.

If you need to read iterating keywords that repeat with a different index value throughout the header, write:

`$fits.iterate.base_keyword`

where `base_keyword` is the name of the keyword sans any index value, e.g. `VECTOR` would be the base of iterating keywords of the form `VECTORn`. (The iterate flag ensures there is no conflict between a base keyword and a keyword that happens to shares the same name, e.g. `NAXIS` for `NAXIS1` and `NAXIS2`.) The pointer will contain an array of all the values found which you can loop through as needed.

To access the bracketed `[unit]` in a FITS keyword's comment field, write:

`$fits.unit.KEYWORD`

### PDS3 Keywords
This is mostly unproblematic. To point to a keyword within a PDS3 nested object, write:

`$label.OBJECT.KEYWORD`

`OBJECT` is whatever is at the end of the "OBJECT = " line of the object you're looking for, and `KEYWORD` is the keyword inside that object.

If a keyword or object has multiple instances in an object/label, they will be stored in the appropriate pointer as arrays and can be accessed like so:

`$label.KEYWORD[index]` (0-indexed)

For keywords with a `<unit>` in their value, the numeric value and unit are accessed separately in the template file. To get the value, write:

`$label.KEYWORD.value`

To get the `<unit>`, write:

`$label.KEYWORD.unit`

Some PDS3 keywords are not valid variable names in Velocity/Java. To point to these keywords in a template, a substitute variable name is required. Common substitutes are defined in [var_sub.json](src/kwex/resources/var_sub.json). More substitutes can be added to this file. Each entry begins with a substitute string that will be used in the template file, followed by the `pos` parameter, which indicates where the substitute string appears in a variable name (`start`, `in`, or `end`), and the `sub` parameter, which is the string in the PDS3 keyword that needs replacing.

For example, PDS3 keywords such as `^Header` are not valid variable names in Java due to the `^` character. The first entry in var_sub.json indicates that you can subtitute in `PTR_` in place of `^` at the beginning of a variable name.

### SPICE Keywords
The "source" for SPICE keywords is [spice_equations.json](src/kwex/resources/spice_equations.json). This file maps keywords to SPICE equations necessary for computing the values of those keywords. A SPICE metakernel file (as well as all the kernels it references and the spiceypy library) is necessary to perform these calculations. You can specify a different (or updated) calculation file via config options. It can be updated to include more keywords/equations, but a very limited number of functions and variables are available for use. See [names_and_functions.txt](names_and_functions.txt) for a list.

### Java HashMaps and ArrayLists
If your extracted keyword values aren't directly analogous to attributes in your template, you can make use of the Java tools underneath the Velocity engine. In Velocity, a hashmap can be defined like so:
```
#set ( $mapName = { "key1" : "value1",
                    "key2" : "value2",
                    "key3" : "value3" } )
```				
and so on. These maps can even be nested for situations in which one variable sets the value for multiple other variables. To access a map value, you can write:

`$mapName.key`, `$mapName[key]`, or `$mapName.get(key)`

Similarly, ArrayLists contain a list of values that can be accessed by index. To define one, write:

```
#set ( $arrayName = [value1, value2, value3] )
```

and access them with:

`$arrayName[index]` (0-indexed)

These maps and arrays can be included anywhere in your template (before the variables they define are used), or stored outside it and imported with the following command:

`#parse(filename.vm)`

Again, be sure to include the parse statement before the variables it defines are required.

## Credit
The SPICE routines in this tool were adapted from code written by Benjamin Sharkey, Senior Faculty Specialist at UMD, with contributions from Adeline Gicquel-Brodtke, Senior Faculty Specialist at UMD.

## Contact Info
For any questions or issues, contact Ben Hirsch of the PDS Small Bodies Node at bhirsch1@umd.edu.

## Installation

Clone or otherwise download this repo, unzip, and run either [insall-kwex.bat](insall-kwex.bat) or [install-kwex.sh](install-kwex.sh) depending on your system. This will create an executable command-line tool for running the main kwex script. Python >3.11 is required along with `regex`, `numpy`, `astropy`, `spiceypy`, and `simpleeval`.

kwex uses the Java-based Apache Velocity template engine. All necessary `.jar` files are included in the [java](src/velocity/java) directory, but you will need some Java Runtime Environment installed.
