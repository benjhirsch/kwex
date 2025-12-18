from state import run_state
from config import get_config
from names import ConfigKey
from .pds3 import get_lbl, get_lbl_values
from .fits import get_fits, get_fits_values
from .spice import get_spice_values

def get_values(product: dict, var_list: dict) -> dict:
    """ Container function for parsing source keyword values corresponding to template variables """
    spice_eqns = run_state.spice_eqns
    run_state.bad_output = False

    lbl_kws = get_lbl(product)
    fits_kws = get_fits(product)

    val_list = {}
    val_list.update(get_lbl_values(var_list, lbl_kws))
    val_list.update(get_fits_values(var_list, fits_kws))       
    val_list.update(get_spice_values(var_list, fits_kws, spice_eqns))

    if get_config(ConfigKey.OUTPUT_CHECK) and run_state.bad_output:
        run_state.bad_output_list.append(run_state.output_list[-1])

    return val_list