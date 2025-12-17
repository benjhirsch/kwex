import regex as re
from astropy.io import fits

from names import Source
from loggers.logger import get_logger
from loggers.interrupter import warning_handler
from utils.values import add_to_val
from utils.products import Product

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
    val_list = {Source.FITS: {}}

    for ext, keyword in var_list[Source.FITS]:
        #identify FITS keyword extension, with none being 0
        ext_num = 0 if ext is None else int(ext)
        hdr = fits_kws[ext_num]
        
        if keyword in hdr:
            val_container = lambda x: hdr[x]
        else:
            val_container = lambda x: {kw_idx: hdr[keyword+kw_idx] for kw_idx in get_iterative(x, hdr)}

        if ext is None:
            template_keyword = keyword
            val_func = val_container
        elif ext.isnumeric():
            template_keyword = f'ext{ext}'
            val_func = lambda x: {x: val_container(x)}

        val_list[Source.FITS].update(add_to_val(keyword=template_keyword, val_func=val_func, func_var=keyword))

    return val_list

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
