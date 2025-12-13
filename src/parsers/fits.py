import regex as re
from astropy.io import fits
from collections import defaultdict

from names import Source
from loggers.logger import get_logger
from loggers.interrupter import warning_handler
from utils.values import add_to_val

def get_fits(product: dict) -> dict:
    """ Wrapper for astropy.fits, returning the header objects in  FITS file. """
    if Source.FITS in product:
        fit = product[Source.FITS]
        get_logger().info(f'Reading FITS file {fit.name}...')
        try:
            with fits.open(fit) as f:
                return [h.header for h in f]
        except:
            warning_handler(f'{fit.name} is not a valid FITS file.')
    return {}
    
def get_fits_values(var_list: dict, fits_kws: dict) -> dict:
    """ Function that finds values of FITS header keywords corresponding to Velocity template variables. Handles multiple extensions. Iterates through keywords with index values. """
    val_list = defaultdict(lambda: {})

    for ext, keyword in var_list[Source.FITS]:
        #identify FITS keyword extension, with none being 0
        if ext is None:
            ext_num = 0
            fits_str = 'fits'
        elif ext.isnumeric():
            ext_num = int(ext)
            fits_str = f'fits_{ext}'

        #find iterative FITS keywords
        try:
            iter_list = [fits_kws[ext_num][kw] for kw in fits_kws[ext_num] if re.sub(r'\d', '', kw) == keyword]
        except:
            iter_list = []

        if len(iter_list) > 1:
            val_list = add_to_val(val_list, fits_str, keyword, val_func=lambda: iter_list)
        else:
            val_list = add_to_val(val_list, fits_str, keyword, val_func=lambda x: fits_kws[ext_num][x])

    return val_list