import shutil

from constants import *
from names import ConfigKey, ConfigState, Source
from loggers.logger import get_logger
from loggers.interrupter import error_handler, warning_handler
from config import get_config
from state import run_state
from .sources import get_input

def product_difference(set1: set, set2: set) -> set:
    """ Helper function that returns the output of a difference operation between two sets of files with extensions removed. """
    return set(s1.with_suffix('') for s1 in set1) - set(s2.with_suffix('') for s2 in set2)

def add_unspecified(set1: set, set2: set, ext: str) -> set:
    """ Helper function that finds the complementary files (same filename, different extension) present in set1 that are missing in set2 and adds them (with the appropriate extension) to set2. """
    unspecified_set = product_difference(set1, set2)
    for un in unspecified_set:
        for s in EXTENSIONS[ext]:
            file = un.with_suffix(s)
            if file.is_file():
                set2.add(file)
                continue
    return set2

def add_unpaired(unpaired_set: set, file_root: dict, file_type: str) -> list:
    """ Helper function that adds singleton products to product list. """
    #if config is set to allow products with only one file (missing either fits or label), add those singleton files to the product list
    un_list = []
    type_switch = [Source.PDS3, Source.FITS]
    if len(unpaired_set) > 0:
        if not get_config(ConfigKey.ALLOW_UNPAIRED):
            #if unpaired files are not allowed and found, issues a warning. if warning is to set to error, the program will end.
            warning_handler(f'Unpaired {file_type} files found.')
        else:
            #otherwise just let the user know, because even if you're allowing it, it's weird.
            get_logger().info(f'Unpaired {file_type} files found.')
        for un in unpaired_set:
            un_list.append({file_type: file_root[un], type_switch[type_switch.index(file_type)^1]: None})
    return un_list

def set_root(file_set: set) -> dict:
    """ Helpfer function to link a file root (full path sans extension) with its extension so the root can be compared to files with the same root. """
    file_root = {}
    for file in file_set:
        file_root[file.with_suffix('')] = file
    return file_root

def get_products(lbl_set: set, fits_set: set) -> list:
    """ Parser that returns a list of paired files comprising a PDS3 object: PDS3 label and FITS data file """
    product_list = []

    if get_config(ConfigKey.FIND_PAIR):
        #allows you to only specify .fits or .lbl files and still get the full PDS3 product
        lbl_set = add_unspecified(fits_set, lbl_set, Source.PDS3)
        fits_set = add_unspecified(lbl_set, fits_set, Source.FITS)

    fits_root = set_root(fits_set)
    lbl_root = set_root(lbl_set)
    #get products that have both a fits file and label file
    paired_input = set(f.with_suffix('') for f in fits_set) & set(l.with_suffix('') for l in lbl_set)
    
    for p in paired_input:
        #add those products to the product list
        product_list.append({Source.PDS3: lbl_root[p], Source.FITS: fits_root[p]})

    #find and add unpaired products if that's allowed
    unpaired_lbl = product_difference(fits_set, lbl_set)
    unpaired_fits = product_difference(lbl_set, fits_set)

    product_list += add_unpaired(unpaired_lbl, lbl_root, Source.PDS3)
    product_list += add_unpaired(unpaired_fits, fits_root, Source.FITS)

    error_handler(lambda: len(product_list) > 0, 'No input products found.')
    get_logger().info(f'{len(product_list)} products identified.')

    return product_list

def get_output(product: dict) -> Path:
    """ Utility that constructs an output Path object from an input product """
    ext = get_config(ConfigKey.OUTPUT_EXT)
    output = run_state.args.output
    first_product = list(product.values())[0].expanduser().resolve()

    if output:
        output_path = Path(output).expanduser().resolve()
        if len(output_path.suffix) > 0:
            #for --output argument of path/to/file.ext, just return that (very bad option if you have multiple input files)
            output_return = output
        else:
            error_handler(lambda: output_path.is_dir(), f'{output_path.as_posix()} is not a valid directory.')
            #for path/to/directory argument, preserve directory structure after input root
            input_root = run_state.input_root
            if input_root:
                input_root = Path(input_root).expanduser().resolve()
                error_handler(lambda: input_root.is_dir(), f'{input_root.as_posix()} is not a valid directory.')

                input_rel = first_product.relative_to(input_root)
                output_plus_input = (output_path / input_rel).with_suffix(ext)
                output_plus_input.parent.mkdir(parents=True, exist_ok=True)

                output_return = output_plus_input
            else:
                #if no valid input root, just append product filename to output path
                output_return = output_path / first_product.with_suffix(ext).name
    else:
        #it no output argument given, send output to product location with output extension
        output_return = first_product.with_suffix(ext)
    
    run_state.output_list.append(output_return)

    if not get_config(ConfigKey.DATA_OUTPUT) == ConfigState.IGNORE:
        data_product = get_data_product(product)
        if data_product:
            data_output = output_return.with_suffix(data_product.suffix)
            verb = {ConfigState.COPY: 'Copy', ConfigState.MOVE: 'Mov'}[get_config(ConfigKey.DATA_OUTPUT)]
            get_logger().info(f'{verb}ing {data_product.name} to {data_output.parent.as_posix()}...')
            shutil.copy2(data_product.as_posix(), data_output.as_posix())
                
    return output_return

def get_data_product(product):
    """ Helper that gets the fits file for a product """
    if Source.FITS in product:
        return product[Source.FITS]
    
def get_input_root(product_list: list[dict]) -> Path:
    """ Utility to determine last common root directory of product list. """
    if len(product_list) > 1:
        parts_list = [list(product.values())[0].parts for product in product_list]

        common_parts = []
        for part in zip(*parts_list):
            if len(set(part)) == 1:
                common_parts.append(part[0])
            else:
                break

        input_root = Path(*common_parts).expanduser().resolve()
        if input_root == Path('/') or len(input_root.parts) < 2:
            warning_handler('Ambiguous input root from --input parameter. Specify with --input-root parameter.')

        return input_root
    
def get_files():
    """ Container function that gets source files and product list from command-line arguments """
    input = run_state.args.input
    input_root = run_state.args.input_root

    lbl_set, fits_set = get_input(input)
    product_list = get_products(lbl_set, fits_set)
    run_state.input_root = input_root or get_input_root(product_list)

    return product_list