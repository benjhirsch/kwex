import re
from collections import defaultdict, OrderedDict

from ..constants import *
from ..names import Source, PointerFlag, PDS3
from ..loggers import *
from ..utils.values import add_to_val

#regex patterns
LIST_PATTERN = re.compile(r'(\((.*)?\))|(\{(.*)?\})') #string enclosed in parentheses or curly brackets
UNIT_PATTERN = re.compile(r'^(.*?)\s*<(\w+)>') #1+ alphanumeric characters enclosed in angle brackets

#start and stop codons for multi-line values
MCHAR = {'(': ')', '{': '}', '"': '"'}

def _format_arbitrary_v(v: str, unit_flag, listed=False):
    """ Utility for parsing PDS3 keyword value strings with arbitrary structure into lists or dictionaries of values. """
    vstrip = v.strip().replace('\n', '').replace('\t', '')
    if not listed and re.match(LIST_PATTERN, vstrip):
        #separate parenthetical lists into lists and send each element through _format_arbitrary_v individually
        v = [_format_arbitrary_v(e.strip(), unit_flag, listed=True) for e in v[1:-1].split(',')]
    elif not v.startswith('"') and unit_flag:
        #turn values of the form "VALUE <UNIT>" into dictionaries with value and unit keys
        unit_match = re.search(UNIT_PATTERN, v)
        try:
            v = {PDS3.VALUE: unit_match.group(1), PDS3.UNIT: unit_match.group(2)} #the string before whitespace and characters enclosed in angle brackets, plus 1+ alphanumeric characters enclosed in angle brackets
        except:
            pass

    return v

def _add_kv(kvd: dict, k: str, v) -> dict:
    """ Utility for assigning a value to a keyword, handling whether it should be added as a scalar or a list item """
    if k not in kvd:
        #if the keyword isn't in the dictionary, add it and assign value to it
        kvd[k] = v
    else:
        try:
            #if it is in the dictionary, try appending to it as if it were a list
            kvd[k].append(v)
        except AttributeError:
            #if it's not a list, turn it into one consisting of the first value and the new one
            kvd[k] = [kvd[k], v]

    return kvd

def _read_line_check(k: str, v: str, olvl: str, plvl, pl: dict) -> bool:
    """ Helper function to check whether a line from the label needs to be read for parsing purposes """
    if v == '':
        #don't parse blank value strings
        return False
    if len(pl[olvl]) == 0:
        #if the pointer list has nothing to say about this level, either it wasn't supplied (so parse everything) or we're at the end of a nested object pointer and may need whatever it contains
        return True
    if k in pl[olvl] and olvl == plvl:
        #parse lines if they contain template keywords where we are
        return True
    if k in (PDS3.OBJECT, PDS3.END_OBJECT):
        #parse lines if we need to get into or out of an objct
        return True
    
def _object_level(ostack, level=0):
    """ Helper function to get current depth in an arbitrarily nested label """
    if len(ostack) > level:
        return list(ostack.keys())[-(1+level)]
    else:
        return PDS3.FLAT

def get_lbl(label: Path, pointer_list=defaultdict(dict)) -> dict:
    """ PDS3 label parser. Reads file and returns dictionary of keyword:value pairs. Handles objects of arbitrary depth and multi-line value strings. Preserves format of text fields with whitespace. """
    info_logger('Reading PDS3 label %s', label.name)

    kv_dict = {} #keyword:value dictionary constructed by parsing the label
    ostack = OrderedDict() #hierarchically ordered dictionary for tracking nested objects
    pseudo_level = PDS3.FLAT #depth based on what line we're at rather than what's actually being parsed

    with open(label) as f:
        for line in f:
            #split each line into tidy keyword=value pairs
            kfull, _, vfull = line.partition('=')
            k = kfull.strip()
            v = vfull.strip()

            if _read_line_check(k, v, _object_level(ostack), pseudo_level, pointer_list):
                #multi-line values will start with (, {, or "
                if v.startswith(tuple(MCHAR.keys())):
                    mstop = MCHAR[v[0]] #multi-line ends with closing version of what it opened with
                    first_line = True
                    current_line = v
                    multi_line = [v]
                    
                    while mstop not in current_line or (first_line and mstop == '"' and current_line.count(mstop) == 1):
                        #iterate through lines until you get to the stop character, but make sure you keep going if the first line just has one "
                        current_line = next(f)
                        multi_line.append(current_line.rstrip())
                        #and add each successive line to the multi-line value
                        first_line = False
                    v = '\n'.join(multi_line)
                elif k == PDS3.OBJECT:
                    #at the start of a new object, add to the object stack and return to the top of the loop
                    if _read_line_check(v, None, _object_level(ostack), pseudo_level, pointer_list):
                        #when entering an object, the value part of the kw=val pair is what we're looking for in the pointer list
                        ostack[v] = {}
                    pseudo_level = v
                    continue
                elif k == PDS3.END_OBJECT:
                    #at the end of an object, remove the most recent object from the stack and assign it to the kw=val pair
                    pseudo_level = _object_level(ostack, 1)
                    if v == _object_level(ostack):
                        k, v = ostack.popitem()

                try:
                    v = _format_arbitrary_v(v, pointer_list[_object_level(ostack)][k][PointerFlag.UNIT])
                except:
                    pass

                if ostack:
                    ostack_top = _object_level(ostack)
                    ostack[ostack_top] = _add_kv(ostack[ostack_top], k, v)
                    #if we're in an object, this line's kw=val pair is added to the object instead of the label dictionary
                else:
                    kv_dict = _add_kv(kv_dict, k, v)

    return kv_dict
    
def get_lbl_values(pointer_list: dict, lbl_kws: dict) -> dict:
    """ Function that finds values of PDS3 label keywords corresponding to Velocity template variables. Performs substitution to convert variables back into PDS3 format in cases where the PDS3 keyword string would not be a valid Java/Velocity variable. """
    info_logger('Extracting values of $label.KEYWORD template pointers from PDS3 label')
    val_list = {Source.PDS3: {}}

    for pointer in pointer_list[PDS3.FLAT].keys():
        try:
            #turn keywords back into their template-friendly version for merging
            template_kw = pointer_list[PDS3.FLAT][pointer][PDS3.TEMPLATE_KW]
            val_list[Source.PDS3].update(add_to_val(keyword=template_kw, val_func=lambda x: lbl_kws[x], func_var=pointer))
        except:
            pass

    return val_list
