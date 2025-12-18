from pathlib import Path
from glob import glob
import regex as re

from config import get_config
from constants import *
from names import ConfigKey, Source
from loggers.interrupter import warning_handler, error_handler

def source_id(file):
    ext = file.suffix
    for s in EXTENSIONS:
        if ext.lower() in EXTENSIONS[s]:
            return s
    warning_handler(f'{file.name} does not have a valid extension for a source file.')
    return False

def source_check(source, sid, check=False):
    file_status = not check or source.is_file()
    if not file_status:
        warning_handler(f'{source.name} is not a valid file.')
    return sid and file_status

def source_iter(source_list, check=False):
    added_set = set()
    for s in source_list:
        if not isinstance(s, Path):
            s = Path(s.strip())
        sid = source_id(s)
        if source_check(s, sid, check):
            added_set.add(s)
    
    return added_set

def get_input(input: list) -> tuple[set, set]:
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

        warning_handler(f'Invalid --input parameter {i}')

    error_handler(lambda: len(source_set) > 0, 'No source products found.')

    return source_set

def check_kernel(kernel: str):
    """ Utility to modify a metakernel's PATH_VALUE keyword to match the its physical location. """
    kernel_path = Path(kernel)
    if not kernel_path.is_file():
        warning_handler(f'SPICE kernel {kernel_path.name} not found.')

    #check if kernel PATH_VALUE is relative or wrong and switch to absolute and correct
    if kernel_path.suffix == '.tm':
        #only relevant for metakernels
        kernel_text = kernel.read_text()
        kernel_path_value = Path(re.search(r"PATH_VALUES\s+=\s+\(\n\s+'(.+)'", kernel_text).group(1))
        kernel_path_repl = kernel_path.parent / 'data'
        
        if not (kernel_path_value.is_absolute() or kernel_path_value == kernel_path_repl):
            kernel_text_repl = re.sub(r"(?<=PATH_VALUES\s+=\s+\(\n\s+').+(?=')", kernel_path_repl.posix, kernel_text)
            kernel_path.write_text(kernel_text_repl)