from ..state import run_state
from ..config import get_config
from ..names import ConfigKey, Source
from .pds3 import get_lbl, get_lbl_values
from .fits import get_fits, get_fits_values

def get_values(product: dict, var_list: dict) -> dict:
    """ Container function for parsing source keyword values corresponding to template variables """
    run_state.bad_output = False
    val_list = {}
    var_check = {s: len(var_list[s]) > 0 for s in iter(Source)}

    if var_check[Source.PDS3] and product.files[Source.PDS3] is not None:
        lbl_kws = get_lbl(product.label)
        val_list.update(get_lbl_values(var_list[Source.PDS3], lbl_kws))
    
    if var_check[Source.FITS] or var_check[Source.SPICE] and product.files[Source.FITS] is not None:
        hdul = get_fits(product.data_product)
        if var_check[Source.FITS]:
            val_list.update(get_fits_values(var_list, hdul))
        if var_check[Source.SPICE]:
            from .spice import get_spice_values
            val_list.update(get_spice_values(var_list, hdul[0].header, run_state.spice_eqns))

    if get_config(ConfigKey.OUTPUT_CHECK) and run_state.bad_output:
        run_state.bad_output_list.add(run_state.output_list[-1])

    return val_list
