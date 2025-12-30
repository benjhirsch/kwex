# Changelog

## [3.0.0] - 2025-12-30

### Added

- Local (pip) installation via `.bat`/`.sh` installaion files and creation of a command-line executable
- Configuration options, viewable with command `kwex get_config` and saveable to a local config file with command `kwex set_config`
- CLI option to override default config options at runtime
- CLI option to specify a root input directory below which to copy directory structure for output products
- Option to copy or move data products to output directory
- `Warning`-level logging which, depending on config options, acts like errors, console messages, or normal log info
- Output (non-PDS) validation for kwex/Velocity template failures
- Exposed, high-level functions for computing common PDS4 SPICE geometry attributes
- Recursive directory search option (without glob patterns) for source input products
- Input argument now allows for a list of files with syntax `@file_list.txt`
- Option to parse `[unit]` in FITS header comment fields via `unit` flag in Velocity template pointer ([#3](https://github.com/benjhirsch/kwex/issues/3))
- Regression test files (template, source files, output success files), which can be found in the [tests](tests) directory
- Option for script execution without activating the template engine
- Support for non-J2000 inertial reference frame SPICE computations
- Centralized modules for project-wide constants, symbolic identifiers, and persistent runtime variables
- [CHANGELOG.md](CHANGELOG.md) and formal release structure
- Bug and Feature issue templates

### Fixed

- `add_kv` PDS3 parser function adjusted so that list keywords with whitespace are properly captured
- Fixed bug preventing users from iteratively parsing FITS keywords with previously used base names ([#4](https://github.com/benjhirsch/kwex/issues/4)). To iteratively parse FITS keywords now, use syntax `$fits.iterate.keyword` (for all cases, not just those with possible conflicts).
- Added regex to list of project dependencies

### Changed

- Basic command is now `kwex path/to/template/file path/to/input/files`
- Most CLI options moved to config options
- Project directory structure changed completely
- Default JSON values file location is now coincident with its respective output file
- Input files are no longer strictly FITS files. User can specify FITS, PDS3 label, or nothing (a directory), and the relevant files will be found.
- Syntax for Velocity template pointers to FITS keywords in extensions changed to `$fits.extN.KEYWORD`. Primary extension is still `$fits.KEYWORD`.
- Syntax for iterating FITS keywords in Velocity template now `$fits.iterate.KEYWORD`
- Updated [README.md](README.md) and [examples.vm](templates/examples.vm)
- `KEYWORD NOT FOUND`/`KEYWORD NOT RECALCULATED` template failures should now provide more useful debugging information via the logging module
- Project-supplied JSON [equations](src/kwex/resources/spice/spice_equations.json) file now uses simplified, high-level `SpiceWrapper` functions, but lower-level functions and variables are still available. See [names_and_functions.txt](names_and_functions.txt) for details.
- Syntax for project-supplied [instr_frame_params.json](src/kwex/resources/spice/instr_frame_params.json) changed to eliminate opaque `rot_90` parameter. Clock angle computations now depend on `instr_uv_plane` parameter with format `["+v", "+u", ""]`. This 3-element list specifies which instrument frame axis (`x, y, z` respectively) corresponds to the horizontal and vertical axes on the image plane (`u` and `v` respectively) and which direction along that axis is positive.
- Temporary metakernel with corrected PATH_VALUES now created at runtime instead of modifying supplied metakernel
