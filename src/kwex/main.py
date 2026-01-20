from .config import get_config
from .names import ConfigKey, ConfigState
from .state import run_state
from .loggers import *
from .parsers import *
from .parsers.spice import init_spice
from .utils import *
from .velocity import *

def kwex_script(args):
    """ Function that contains the kwex workflow. """
    init_log()
    compile_velocity()

    product_list = get_files(args.input, args.input_root)
    pointer_list = get_pointers(args.template)
    write_nows_template(run_state.nows_template_str)
    init_spice(pointer_list)
    init_velocity(run_state.nows_template_filename)
    
    for product in product_list.values():
        output_path = get_output(args.output, product)
        val_list = get_values(product, pointer_list)
        send_values(val_list, output_path)

        if get_config(ConfigKey.DATA_OUTPUT) == ConfigState.MOVE:
            product.data_product.unlink()

    terminate_velocity()
    log_bad_output()
    run_state.nows_template_filename.unlink()
    if run_state.temp_kernel:
        run_state.kernel_path.unlink()
