from .config import get_config
from .names import ConfigKey, ConfigState
from .state import run_state
from .loggers.logger import init_log
from .velocity.processor import compile_velocity, run_velocity
from .utils.products import get_files, get_output
from .parsers.template import get_vars
from .parsers.spice import init_spice
from .parsers.values import get_values
from .utils.java import wait_process
from .loggers.interrupter import log_bad_output

def run_kwex():
    """ Function that contains the kwex workflow. """
    init_log()
    compile_velocity()

    product_list = get_files()
    var_list = get_vars()
    init_spice(var_list)
    
    for product in product_list.values():
        output_path = get_output(product)
        val_list = get_values(product, var_list)
        run_velocity(val_list, output_path)

        if get_config(ConfigKey.DATA_OUTPUT) == ConfigState.MOVE:
            product.data_product.unlink()

    wait_process(run_state.velocity_process)
    log_bad_output()
    run_state.nows_template_filename.unlink()
    if run_state.temp_kernel:
        run_state.kernel_path.unlink()
    if not get_config(ConfigKey.KEEP_JSON):
        for jv in run_state.json_list:
            jv.unlink()