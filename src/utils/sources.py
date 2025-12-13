from pathlib import Path
from glob import glob
import regex as re

from config import get_config
from constants import *
from names import ConfigKey, Source
from loggers.interrupter import warning_handler, error_handler

def get_input(input: list) -> tuple[set, set]:
    """ Utility that takes --input parameter and constructs two sets of files: one of PDS3, one of FITS 
    
    Supports: individual files, multiple positional files, directories, glob patterns, ~ expansion, and @file.ext w/ list of input files"""
    lbl_set = set()
    fits_set = set()

    for i in input:
        if i.startswith('@'):
            at_arg = Path(i[1:]).expanduser().resolve()
            if at_arg.is_file():
                with at_arg.open() as fa:
                    at_input = fa.readlines()
                for a in at_input:
                    a_path = Path(a.strip())
                    if a_path.is_file():
                        classify_file(a_path, lbl_set, fits_set)
                    else:
                        warning_handler(f'{a_path.as_posix()} in {i[1:]} is not a valid file.')
            continue

        input_path = Path(i).expanduser().resolve()
        if any(glob_char in i for glob_char in '*?[]{}'):
            input_glob = glob(i, recursive=True)
            for g in input_glob:
                classify_file(Path(g), lbl_set, fits_set)
            continue

        if input_path.is_dir():
            if get_config(ConfigKey.RECURSIVE_INPUT_DIR):
                input_glob = input_path.rglob('*')
                for g in input_glob:
                    classify_file(g, lbl_set, fits_set)
            else:
                for child in input_path.iterdir():
                    if child.is_file():
                        classify_file(child, lbl_set, fits_set)
            continue

        if input_path.is_file():
            classify_file(input_path, lbl_set, fits_set)
            continue

        warning_handler(f'Invalid --input parameter {i}')

    error_handler(lambda: len(lbl_set) > 0 or len(fits_set) > 0, 'No input products found.')

    return lbl_set, fits_set

def classify_file(file_path: Path, lbl_set: set, fits_set: set):
    """ Helper function to group input files into PDS3 and FITS sets """
    ext = file_path.suffix.lower()
    if ext in EXTENSIONS[Source.PDS3]:
        lbl_set.add(file_path)
    elif ext in EXTENSIONS[Source.FITS]:
        fits_set.add(file_path)

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