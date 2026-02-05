import shutil
from collections import OrderedDict

from ..constants import *
from ..names import ConfigKey, ConfigState, Source
from ..loggers import *
from ..config import get_config
from ..state import run_state
from .sources import get_input, source_id, source_check
from .errors import error_handler, warning_handler

class Product:
    """ Object that holds an input pair, i.e. a (FITS) data product and corresponding (PDS3) label """
    def __init__(self, path):
        self.root = path.with_suffix('')
        self.files = {Source.PDS3: None, Source.FITS: None}

        self.add_file(path)

    @property
    def data_product(self):
        return self.root.with_suffix(self.files[Source.FITS])
        
    @property
    def label(self):
        return self.root.with_suffix(self.files[Source.PDS3])

    def add_file(self, path, check=False):
        ext = path.suffix
        sid = source_id(path)
        file_added = source_check(path, sid, check)
        if file_added:
            self.files[sid] = ext
        return file_added

    def find_pair(self, source):
        for s in EXTENSIONS[source]:
            pair_path = self.root.with_suffix(s)
            pair_found = self.add_file(pair_path, check=True)
            if pair_found:
                return True
        return False
    
def get_products(source_set: set) -> OrderedDict:
    """ Parser that returns a list of paired files comprising a PDS3 object: PDS3 label and FITS data file """
    product_list = OrderedDict()

    for source in sorted(source_set):
        source_root = source.with_suffix('')
        if source_root in product_list:
            if source_id(source) not in product_list[source_root].files or product_list[source_root].files[source_id(source)] is None:
                product_list[source_root].add_file(source)
        else:
            product = Product(source)
            sid = source_id(source)
            
            if get_config(ConfigKey.FIND_PAIR):
                type_switch = [Source.PDS3, Source.FITS]
                pair_source = type_switch[type_switch.index(sid)^1]
                pair_found = product.find_pair(pair_source)
                if not pair_found:
                    info_logger('Unpaired product %s found', source.name)
                    if not get_config(ConfigKey.ALLOW_UNPAIRED):
                        warning_handler('Removing %s from product list', source.name)

            if not get_config(ConfigKey.FIND_PAIR) or pair_found or get_config(ConfigKey.ALLOW_UNPAIRED):
                product_list[product.root] = product

    for root, product in product_list.copy().items():
        if None in product.files.values():
            info_logger('Unpaired product %s found', Path(root).name)
            if not get_config(ConfigKey.ALLOW_UNPAIRED):
                warning_handler('Removing %s from product list', Path(root).name)
                q = product_list.pop(root)

    error_handler(lambda: len(product_list) > 0, 'No source products found')
    info_logger('%s products identified', len(product_list))

    return product_list

def get_output(output: str, product: Product) -> Path:
    """ Utility that constructs an output Path object from an input product """
    ext = get_config(ConfigKey.OUTPUT_EXT)
    root_path = Path(product.root).expanduser().resolve()

    if output:
        output_path = Path(output).expanduser().resolve()
        if len(output_path.suffix) > 0:
            #for --output argument of path/to/file.ext, just return that (very bad option if you have multiple input files)
            output_return = output_path
        else:
            error_handler(lambda: output_path.is_dir(), '%s is not a valid directory', output_path.as_posix())
            #for path/to/directory argument, preserve directory structure after input root
            input_root = run_state.input_root
            if input_root:
                input_root = Path(input_root).expanduser().resolve()
                error_handler(lambda: input_root.is_dir(), '%s is not a valid directory', input_root.as_posix())

                input_rel = root_path.relative_to(input_root)
                output_plus_input = (output_path / input_rel).with_suffix(ext)
                output_plus_input.parent.mkdir(parents=True, exist_ok=True)

                output_return = output_plus_input
            else:
                #if no valid input root, just append product filename to output path
                output_return = output_path / root_path.with_suffix(ext).name
    else:
        #it no output argument given, send output to product location with output extension
        output_return = root_path.with_suffix(ext)
    
    run_state.output_list.append(output_return)

    if not get_config(ConfigKey.DATA_OUTPUT) == ConfigState.IGNORE:
        data_product = product.data_product
        if data_product:
            data_output = output_return.with_suffix(data_product.suffix)
            verb = {ConfigState.COPY: 'Copy', ConfigState.MOVE: 'Mov'}[get_config(ConfigKey.DATA_OUTPUT)]
            info_logger('%sing %s to %s', verb, data_product.name, data_output.parent.as_posix())
            shutil.copy2(data_product.as_posix(), data_output.as_posix())
                
    return output_return

def _get_input_root(product_list: OrderedDict[Product]) -> Path:
    """ Utility to determine last common root directory of product list. """
    if len(product_list) > 1:
        parts_list = [Path(product).parts for product in product_list]

        common_parts = []
        for part in zip(*parts_list):
            if len(set(part)) == 1:
                common_parts.append(part[0])
            else:
                break

        input_root = Path(*common_parts).expanduser().resolve()
        if input_root == Path('/') or len(input_root.parts) < 2:
            warning_handler('Ambiguous input root from --input parameter. Specify with --input-root parameter')

        return input_root
    
def get_files(input: list, input_root: str):
    """ Container function that gets source files and product list from command-line arguments """
    source_set = get_input(*input)
    product_list = get_products(source_set)
    run_state.input_root = input_root or _get_input_root(product_list)

    return product_list
