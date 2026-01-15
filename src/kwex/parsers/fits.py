import re
from astropy.io import fits
from pathlib import Path
from collections import defaultdict

from ..names import Source, PointerFlag, FITS
from ..loggers import *
from ..utils.values import add_to_val
from ..state import run_state

EXT_PATTERN = re.compile(r'ext(\d+)')
UNIT_PATTERN = re.compile(r'\[(.+)\]')
CHUNK_PATTERN = re.compile(r'([A-Z\-\_]+)(\d*)')

def get_fits(fits_product: Path) -> dict:
    """ Wrapper for astropy.fits, returning the HDUL from a FITS file. """
    info_logger('Reading FITS file %s', fits_product.name)
    fits_obj = defaultdict(dict)
    try:
        with fits.open(fits_product) as f:
            for ext in run_state.fits_hdr_list:
                fits_obj[ext]['header'] = f[ext].header
                if run_state.fits_fileinfo_check:
                    fits_obj[ext][PointerFlag.FILEINFO] = f[ext].fileinfo()
            return fits_obj
    except:
        warning_handler('%s is not a valid FITS file', fits_product.name)
    
def get_fits_values(var_list: dict, fits_obj: dict) -> dict:
    """ Function that finds values of FITS header keywords corresponding to Velocity template variables. Handles multiple extensions. Iterates through keywords with index values. """
    info_logger('Extracting values of $fits.KEYWORD template pointers from FITS file')
    val_list = {}
    iter_list = {}

    for ext in run_state.fits_iter_list:
        iter_list[ext] = _get_iteratives(fits_obj[ext][FITS.HEADER])

    for pointer in var_list[Source.FITS]:
        ext_num = pointer[FITS.EXT_NUM]
        keyword = pointer[FITS.KEYWORD]

        if pointer[PointerFlag.FILEINFO]:
            #with fileinfo flag, extract FITS header metadata retrieved by astropy.io.fits rather than keyword values from the header
            val_func = lambda x: fits_obj[ext_num][PointerFlag.FILEINFO][x]
        else:
            hdr = fits_obj[ext_num][FITS.HEADER]
            if pointer[PointerFlag.UNIT]:
                #units are found in brackets in a keyword's comment field
                val_container = lambda x: re.search(UNIT_PATTERN, hdr.comments[x]).group(1)
            else:
                #otherwise just get the keyword value
                val_container = lambda x: hdr[x]

            if pointer[PointerFlag.ITERATE]:
                #with the iterate flag, the value returned is a dictionary of keyword indices and their respective values rather than a flat value
                val_func = lambda x: {kw_idx: val_container(keyword+kw_idx) for kw_idx in iter_list[ext_num][x]}
            else:
                val_func = val_container

        #because of the nested nature of keywords with pointer flags, we put the keyword and its value into an empty dictionary with the right structure first and then merge it with val_list
        dict_to_merge = add_to_val(keyword=keyword, val_func=val_func)
        for branch in pointer[FITS.TREE]:
            dict_to_merge = {branch: dict_to_merge}
        val_list = _deep_merge(val_list, dict_to_merge)

    return {Source.FITS: val_list}

def _deep_merge(into_dict: dict, dict_to_merge: dict) -> dict:
    """ Helper function that merges one dictionary into another while maintaining original structure and content of the latter """
    for key, value in dict_to_merge.items():
        if isinstance(value, dict):
            into_dict[key] = _deep_merge(into_dict.get(key, {}), value)
        else:
            into_dict[key] = value

    return into_dict

def _get_iteratives(hdr: dict) -> defaultdict:
    """ Helper function for generating a list of iterative FITS keywords. Chunks FITS header keywords into a base and numerical index and returns a list of indexes with bases that match the keyword argument """
    iter_list = defaultdict(list)
    for kw in hdr:
        match = CHUNK_PATTERN.match(kw)
        if match:
            base, idx = match.groups()
            iter_list[base].append(idx)

    return iter_list
