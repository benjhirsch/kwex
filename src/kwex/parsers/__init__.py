# parsers/__init__.py
from .pds3 import get_lbl, get_lbl_values
from .fits import get_fits, get_fits_values
from .template import get_pointers, write_nows_template
from .values import get_values
