# Changelog

## [3.0.0] - 2025-12-17

### Added

- Local installation via `pip` and creation of a command-line executable
- Configuration options, viewable with command `kwex get_config` and saveable to a local config file with command `kwex set_config`
- CLI option to override default config options at runtime
- CLI option to specify a root input directory below which to copy directory structure for output products
- Option to copy or move data products to output directory
- `Warning`-level logging which, depending on config options, acts like errors, console messages, or normal log info
- Output (non-PDS) validation for kwex/Velocity template failures
- Exposed, high-level functions for computing common PDS4 SPICE geometry attributes
- Recursive directory search option (without glob patterns) for source input products
- Input argument now allows for a list of files with syntax `@file_list.txt`
- Option for script execution without activating the template engine
- Support for non-J2000 inertial reference frame SPICE computations
- Centralized modules for project-wide constants, symbolic identifiers, and persistent runtime variables
- [CHANGELOG.md](CHANGELOG.md) and formal release structure

### Changed

- Basic command is now `kwex path/to/template/file path/to/input/files`
- Most CLI options moved to config options
- Project directory structure changed completely
- Input files are no longer strictly FITS files. User can specify FITS, PDS3 label, or nothing (a directory), and the relevant files will be found.
- Format for Velocity template pointers to FITS keywords in extensions changed to `$fits.extN.KEYWORD`. Primary extension is still `$fits.KEYWORD`.
- Updated [README.md](README.md) and [examples.vm](templates/examples.vm)
- `KEYWORD NOT FOUND`/`KEYWORD NOT RECALCULATED` template failures should now provide more useful debugging information via the logging module
- Project-supplied JSON [equations](resources/spice_equations.json) file now uses simplified, high-level `SpiceWrapper` functions, but lower-level functions and variables are still available. See [names_and_functions.txt](resources/names_and_functions.txt) for details.
- Syntax for project-supplied [instr_frame_params.json](resources/instr_frame_params.json) changed to eliminate opaque `rot_90` parameter. Clock angle computations now depend on `instr_uv_plane` parameter with format `["+v", "+u", ""]`. This 3-element list specifies which instrument frame axis (`x, y, z` respectively) corresponds to the horizontal and vertical axes on the image plane (`u` and `v` respectively) and which direction along that axis is positive.
