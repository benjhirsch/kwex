import regex as re
from astropy.io import fits

from ..names import Source, PointerFlag
from ..loggers.logger import get_logger
from ..loggers.interrupter import warning_handler
from ..utils.values import add_to_val
from ..utils.products import Product

def get_fits(product: Product) -> dict:
    """ Wrapper for astropy.fits, returning the header objects in  FITS file. """
    if product.files[Source.FITS]:
        fit = product.data_product
        get_logger().info(f'Reading FITS file {fit.name}...')
        try:
            with fits.open(fit) as f:
                return [h.header for h in f]
        except:
            warning_handler(f'{fit.name} is not a valid FITS file.')
    return {}
    
def get_fits_values(var_list: dict, fits_kws: dict) -> dict:
    """ Function that finds values of FITS header keywords corresponding to Velocity template variables. Handles multiple extensions. Iterates through keywords with index values. """
    val_list = {}
    for pointer in var_list[Source.FITS]:
        kw_parts = pointer.split('.')
        #the final component for a FITS template pointer is always the keyword
        keyword = kw_parts.pop()

        unit_flag = PointerFlag.UNIT in kw_parts
        iterate_flag = PointerFlag.ITERATE in kw_parts
        ext_flag = re.search(r'ext(\d+)', pointer)
        if ext_flag:
            #get keywords from this extension header if specified by extN
            ext_num = int(ext_flag.group(1))
        else:
            #otherwise get them from the primary header
            ext_num = 0

        hdr = fits_kws[ext_num]

        if unit_flag:
            #units are found in brackets in a keyword's comment field
            val_container = lambda x: re.search(r'\[(.+)\]', hdr.comments[x]).group(1)
        else:
            #otherwise just get th keyword value
            val_container = lambda x: hdr[x]

        if iterate_flag:
            #with the iterate flag, the value returned is a dictionary of keyword indices and their respective values rather than a flat value
            val_func = lambda x: {kw_idx: val_container(keyword+kw_idx) for kw_idx in get_iterative(x, hdr)}
        else:
            val_func = val_container

        #because of the nested nature of keywords with pointer flags, we put the keyword and its value into an empty dictionary with the right structure first and then merge it with val_list
        dict_to_merge = add_to_val(keyword=keyword, val_func=val_func)
        for branch in reversed(kw_parts):
            dict_to_merge = {branch: dict_to_merge}
        val_list = deep_merge(val_list, dict_to_merge)

    return {Source.FITS: val_list}

def deep_merge(into_dict: dict, dict_to_merge: dict) -> dict:
    """ Helper function that merges one dictionary into another while maintaining original structure and content of the latter """
    for key, value in dict_to_merge.items():
        if isinstance(value, dict):
            into_dict[key] = deep_merge(into_dict.get(key, {}), value)
        else:
            into_dict[key] = value

    return into_dict

def get_iterative(keyword: str, hdr: dict) -> list[str]:
    """ Helper function for generating a list of iterative FITS keywords. Chunks FITS header keywords into a base and numerical index and returns a list of indexes with bases that match the keyword argument """
    iter_list = []
    for kw in hdr:
        kw_chunk = re.search(r'([A-Z\-\_]+)(\d*)', kw)
        try:
            kw_base = kw_chunk.group(1)
            kw_idx = kw_chunk.group(2)
        except:
            continue

        if kw_base == keyword:
            iter_list.append(kw_idx)

    return iter_list
