from pathlib import Path
import re
from collections import defaultdict
import json

from ..loggers import *
from ..state import run_state
from ..names import Source, PointerFlag, FITS, PDS3
from ..constants import *

#regex patterns for template strings
#$label.<1+ alpanumeric characters + period seperators for nested objects> optionally enclosed in curly brackets
PDS3_TEMPLATE_PATTERN = re.compile(r'\$(?:\{)?label\.([\w.\(]+)(?:\})?')
#the same, but fits, and the seperators are for pointer tags
FITS_TEMPLATE_PATTERN = re.compile(r'\$(?:\{)?fits\.([\w.\(]+)(?:\})?')
#$spice.<1+ alphanumeric characters>. no period separators needed for spice so far
SPICE_TEMPLATE_PATTERN = re.compile(r'\$(?:\{)?spice\.([\w\(]+)(?:\})?')
#ext<1+ digits> to capture fits header extensions
EXT_PATTERN = re.compile(r'ext(\d+)')
#.<1+alphanumeric characters>( to capture the beginning of a method call and not another part of the pointer object
CALL_PATTERN = re.compile('\.\w+\(')

#PDS3 keyword variable substitution file
VAR_SUB_LIST = json.loads(VAR_SUB_JSON.read_text())
#and dictionary of functions for implementing it
SUB_POSITION_CHECK = {'start': lambda x, y: x.startswith(y), 'in': lambda x, y: x in y, 'end': lambda x, y: x.endswith(y)}

PDS3_POINTER_LIST = defaultdict(dict)

def get_pointers(template: str) -> dict:
    """ Parser that reads a .vm Velocity template file and retrieves variable pointers to PDS3, FITS, and SPICE keywords. """
    vm_str = []
    vm_nows = []
    current_line = []
    in_velocity = False

    template_path = Path(template).expanduser().resolve()
    error_handler(lambda: template_path.is_file(), 'Template file %s not found', template_path.name)

    with open(template) as f:
        for line in f:
            if '$' in line:
                #we only need to get template lines that include variable pointers
                vm_str.append(line)

            vm_nows, current_line, in_velocity = _build_nows_template(line, vm_nows, current_line, in_velocity)

    vm_str = ''.join(vm_str)
    vm_nows = ''.join(vm_nows)

    label_list = _find_vars(PDS3_TEMPLATE_PATTERN, vm_str)
    info_logger('%s PDS3 label keywords found in template', len(label_list))
    for pointer in label_list:
        pointer_parts = pointer.split('.')
        _parse_pds3_pointer(pointer_parts)

    fits_list = _find_vars(FITS_TEMPLATE_PATTERN, vm_str)
    fits_list = [_parse_fits_pointer(p) for p in fits_list]
    info_logger('%s FITS keywords found in template', len(fits_list))

    spice_list = _find_vars(SPICE_TEMPLATE_PATTERN, vm_str)
    info_logger('%s SPICE keywords found in template', len(spice_list))
    if len(spice_list) > 0:
        run_state.fits_hdr_list.add(0)

    run_state.nows_template_filename = template_path.with_name('nows_' + Path(template).name)
    run_state.nows_template_str = vm_nows

    return {Source.PDS3: PDS3_POINTER_LIST, Source.FITS: fits_list, Source.SPICE: spice_list}

def _parse_fits_pointer(pointer_str: str) -> dict:
    """ Utility that breaks a FITS pointer str into period-separated components representing flags and returns an object with those flags applied/registered """ 
    pointer = {}
    pointer_parts = pointer_str.split('.')
    #for fits pointers, the last segment is always the keyword
    pointer[FITS.KEYWORD] = pointer_parts.pop()
    pointer[FITS.TREE] = reversed(pointer_parts)
    
    for flag in PointerFlag:
        pointer[flag] = flag in pointer_parts
    
    ext_flag = re.search(EXT_PATTERN, pointer_str)
    if ext_flag:
        #if an explicit extension number is given, use that
        pointer[FITS.EXT_NUM] = int(ext_flag.group(1))
    else:
        #otherwise assume 0, i.e. the primary HDU
        pointer[FITS.EXT_NUM] = 0

    #global variable to track which fits extensions actually need to be accessed by astropy
    run_state.fits_hdr_list.add(pointer[FITS.EXT_NUM])
    #global variable to track whether we need to get the astropy fileinfo metadata or just the HDU
    run_state.fits_fileinfo_check = run_state.fits_fileinfo_check or pointer[PointerFlag.FILEINFO]
    #global variable to track whether we need to preprocess iterative keywords in any particular HDU
    if pointer[PointerFlag.ITERATE]:
        run_state.fits_iter_list.add(pointer[FITS.EXT_NUM])

    return pointer

def _parse_pds3_pointer(pointer_parts: list, nest=PDS3.FLAT) -> dict:
    """ Utility that registers parts of a PDS3 pointer, including its level in the label, whether it has units, and if has substitute strings """
    pointer = {}
    #for pds3 pointers, the first segment is always the top-level keyword
    keyword = pointer_parts.pop(0)
    
    #check whether a keyword in the template has a known substitute string for a PDS3-native keyword string that wouldn't be valid in Java/Velocity
    kw_repl = keyword
    for template_str in VAR_SUB_LIST:
        position = VAR_SUB_LIST[template_str]['position']
        pds3_str = VAR_SUB_LIST[template_str]['pds3_str']
        if SUB_POSITION_CHECK[position](keyword, template_str):
            #if so, replace keyword variable with the pds3-compliant version for lookup
            kw_repl = kw_repl.replace(template_str, pds3_str)
    #and store the velocity-compliant version for eventual template merging
    pointer[PDS3.TEMPLATE_KW] = keyword
    keyword = kw_repl

    #preregister whether a keyword has a "value <unit>" structure for quicker label parsing
    pointer[PointerFlag.UNIT] = len(pointer_parts) > 0 and pointer_parts[0] in (PDS3.UNIT, PDS3.VALUE)
    q = pointer_parts.pop(0) if pointer[PointerFlag.UNIT] else None

    PDS3_POINTER_LIST[nest][keyword] = pointer

    if pointer_parts:
        #if there are still parts of the pointer left, it's a nested object, so we define another level (below flat) corresponding to the object and put the rest of the keyword there
        _parse_pds3_pointer(pointer_parts, keyword)

def _find_vars(pattern: str, template: str) -> list:
    """ Utility for handling regex search of template for variable pointers. """
    var_list = []
    for match in pattern.finditer(template):
        pointer = match.group(1)

        call_match = CALL_PATTERN.search(pointer)
        if call_match:
            #if a pointer string contains a method call, remove everything from the method call on
            start_call = call_match.span()[0]
            pointer = pointer[:start_call]

        var_list.append(pointer)

    return var_list

def _build_nows_template(line: str, vm_nows: list, current_line: str, in_velocity: bool) -> tuple[str, str, bool]:
    """ For human-readability, users may create templates with lots of whitespace. This function constructs a string of the template whitespace removed so the output looks like nice xml. """
    open_char = ['(', '{', '[']
    close_char = [')', '}', ']']

    lstrip = line.strip()
    if not in_velocity:
        if lstrip.startswith('#'):
            #if at the start of a velocity code block, register that and don't add line
            in_velocity = True
        else:
            #if not in a velocity code block, add line as normal
            vm_nows.append(line)

    if in_velocity:
        #if in a velocity code block, add this line to the overall current line
        current_line.append(lstrip)
        joined_current = ''.join(current_line)
        if (any([c in line for c in close_char]) and sum([joined_current.count(op) for op in open_char]) == sum([joined_current.count(cl) for cl in close_char])) or (any([lstrip == c for c in ['#end', '#else']])):
            #if all parentheses are closed or there's an #end or #else statement, get out of velocity code block
            in_velocity = False
            vm_nows.append('%s##\n' % joined_current)
            current_line = []
    
    return vm_nows, current_line, in_velocity

def write_nows_template(nows_str: str) -> Path:
    """ Utility to write the no whitespace (nows) template file """
    run_state.nows_template_filename.write_text(nows_str)
