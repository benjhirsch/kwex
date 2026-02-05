from pathlib import Path
from glob import glob
import re

from ..config import get_config
from ..constants import *
from ..names import ConfigKey
from ..loggers import *
from ..state import run_state
from .errors import warning_handler, error_handler

def source_id(file):
    """ Utility for checking whether a source product file extension is valid and returning a normalized form. """
    ext = file.suffix
    for s in EXTENSIONS:
        if ext.lower() in EXTENSIONS[s]:
            return s
    warning_handler('%s does not have a valid extension for a source file', file.name)
    return False

def source_check(source, sid, check=False):
    """ Utility for checking whether a source product is a valid file with a valid file extension. """
    file_status = not check or source.is_file()
    if not file_status:
        warning_handler('%s is not a valid file', source.name)
    return sid and file_status

def source_iter(source_list, check=False):
    """ Utility for iterating through a list of files and constructing a set of valid source files. """
    added_set = set()
    for s in source_list:
        if not isinstance(s, Path):
            s = Path(s.strip())
        sid = source_id(s)
        if source_check(s, sid, check):
            added_set.add(s)
    
    return added_set

def get_input(*input) -> set:
    """ Utility that takes --input parameter and constructs two sets of files: one of PDS3, one of FITS 
    
    Supports: individual files, multiple positional files, directories, glob patterns, ~ expansion, and @file.ext w/ list of input files"""
    source_set = set()

    for i in input:
        #read list of files from @file
        if i.startswith('@'):
            at_arg = Path(i[1:]).expanduser().resolve()
            if at_arg.is_file():
                with at_arg.open() as fa:
                    at_input = fa.readlines()
                source_set.update(source_iter(at_input, check=True))
            continue

        input_path = Path(i).expanduser().resolve()
        if any(glob_char in i for glob_char in '*?[]{}'):
            input_glob = glob(i, recursive=True)
            source_set.update(source_iter(input_glob))
            continue

        if input_path.is_dir():
            if get_config(ConfigKey.RECURSIVE_INPUT_DIR):
                input_glob = input_path.rglob('**/*.*')
                source_set.update(source_iter(input_glob))
            else:
                source_set.update(input_path.iterdir())
            continue

        if input_path.is_file():
            source_set.add(input_path)
            continue

        warning_handler('Invalid input parameter %s', i)

    error_handler(lambda: len(source_set) > 0, 'No source products found')

    return source_set

def check_kernel(kernel: str):
    """ Utility to modify a metakernel's PATH_VALUE keyword to match the its physical location. """
    kernel_path = Path(kernel)
    error_handler(lambda: kernel_path.is_file(), 'SPICE kernel %s not found', kernel_path.name)

    #check if kernel PATH_VALUE is relative or wrong and switch to absolute and correct
    if kernel_path.suffix == '.tm':
        #only relevant for metakernels
        kernel_text = kernel.read_text()
        path_values_str = re.search(r"PATH_VALUES\s+=\s+\(\n\s+('.+')", kernel_text).group(1)
        path_values_path = Path(path_values_str[1:-1])
        path_values_repl = kernel_path.parent / 'data'
        path_values_repl_str = f"'{path_values_repl.as_posix()}'"
        
        if not (path_values_path.is_absolute() or path_values_path == path_values_repl):
            kernel_text_repl = kernel_text.replace(path_values_str, path_values_repl_str)
            info_logger("Invalid PATH_VALUES in %s. Writing temporary metakernel with PATH_VALUES %s", kernel_path.name, path_values_repl_str)
            temp_kernel = kernel_path.with_stem(f'temp_{kernel_path.stem}')
            temp_kernel.write_text(kernel_text_repl)
            kernel_path = temp_kernel
            run_state.temp_kernel = True
            run_state.kernel_path = temp_kernel

    return kernel_path

def cleanup():
    """ Utility for deleting temporary files at program end. """
    try:
        run_state.nows_template_filename.unlink()
    except:
        pass
    if run_state.temp_kernel:
        run_state.kernel_path.unlink()
