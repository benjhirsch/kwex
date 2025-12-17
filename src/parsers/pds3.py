import regex as re
import json

from constants import *
from names import Source
from loggers.logger import get_logger
from utils.values import add_to_val
from utils.products import Product

def add_kv(kvd: dict, k: str, v: str) -> dict:
    """ Utility for parsing PDS3 label keyword=value pairs with arbtirary structure into a dictionary of keyword:value pairs. Handles lists of values, values with units, and values with reserved XML characters. """
    if isinstance(v, str):
        if re.match(r'(\((.*)?\))|(\{(.*)?\})', v.strip()): #string enclosed in parantheses or curly brackets
            #separate parenthetical lists into lists
            listv = [e.strip() for e in v.strip()[1:-1].split(',')]
            #send each element through add_kv individually
            v = [add_kv({}, n, elem)[n] for n, elem in enumerate(listv)]
        elif not v.startswith('"') and re.search(r'<\w+>', v): #1+ alphanumeric characters enclosed in angle brackets
            #turn values of the form "VALUE <UNIT>" into dictionaries with value and unit keys
            try:
                v = {'value': re.search(r'^(.*?)\s*<.*?>', v).group(1), 'unit': re.search(r'<\w+>', v).group(0)[1:-1]} #the string before whitespace and characters enclosed in angle brackets, plus 1+ alphanumeric characters enclosed in angle brackets
            except:
                pass
        else:
            #reserved XML character replacement
            for c in RESERVED_XML_CHARS:
                pattern = r'\%s(?!.*;)' % c #reserved character not followed by 0+ other characters and then a semi-colon
                v = re.sub(pattern, '&%s;' % RESERVED_XML_CHARS[c], v)

    if k in kvd:
        #if a keyword is already in the dictionary, either turn the value into a list or add to the value list already there
        if not isinstance(kvd[k], list):
            kvd[k] = [kvd[k]]
        kvd[k].append(v)
    else:
        kvd[k] = v

    return kvd

def get_lbl(product: Product) -> dict:
    """ PDS3 label parser. Reads file and returns dictionary of keyword:value pairs. Handles objects of arbitrary depth and multi-line value strings. Preserves format of text fields with whitespace. """
    if product.files[Source.PDS3]:
        label = product.label
        get_logger().info(f'Reading PDS3 label {label.name}...')

        kv_dict = {}
        ostack = []
        mchar = {'(': ')', '{': '}', '"': '"'}

        with open(label) as f:
            lbl_lines = [line for line in f]

        for n, line in enumerate(lbl_lines):
            #split each line into tidy keyword=value pairs
            k, v = ([p.strip() for p in line.split('=')][:2] + [None]*2)[:2]

            if v is not None:
                #multi-line values will start with (, {, or "
                if v.startswith(tuple(mchar.keys())):
                    mstop = mchar[v[0]] #multi-line ends with closing version of what it opened with
                    ml_count = n
                    current_line = v
                    while mstop not in current_line or (ml_count == n and v == '"'):
                        #iterate through lines until you get to the stop character, but make sure you keep going if the first line is just a "
                        ml_count += 1
                        current_line = lbl_lines[ml_count]
                        v += ' %s' % current_line
                        #and add each successive line to the multi-line value
                elif k == 'OBJECT':
                    #at the start of a new object, add to the object stack and return to the top of the loop
                    ostack.append([v, {}])
                    continue
                elif k == 'END_OBJECT':
                    k, v, = ostack.pop()
                    #at the end of an object, remove the most recent object from the stack and assign it to the kw=val pair
                elif v == '':
                    v = lbl_lines[n+1]

                if ostack:
                    ostack[-1][-1] = add_kv(ostack[-1][-1], k, v)
                    #if we're in an object, this line's kw=val pair is added to the object instead of the label dictionary
                else:
                    kv_dict = add_kv(kv_dict, k, v)

        return kv_dict
    
def get_lbl_values(var_list: dict, lbl_kws: dict) -> dict:
    """ Function that finds values of PDS3 label keywords corresponding to Velocity template variables. Performs substitution to convert variables back into PDS3 format in cases where the PDS3 keyword string would not be a valid Java/Velocity variable. """
    sub_check = {'start': lambda x: '^%s' % x, 'in': lambda x: x, 'end': lambda x: '%s$' % x}
    val_list = {Source.PDS3: {}}

    #load PDS3 keyword variable substitution file
    with VAR_SUB_LIST.open() as f:
        var_sub_list = json.load(f)

    for template_keyword in var_list[Source.PDS3]:
        pds3_keyword = template_keyword
        for sub in var_sub_list:
            #for each possible variable substitution, check if the Java sub is in the right place, then replace with PDS3 original
            pds3_keyword = re.sub(sub_check[var_sub_list[sub]['pos']](sub), var_sub_list[sub]['sub'], pds3_keyword)

        val_list[Source.PDS3].update(add_to_val(keyword=template_keyword, val_func=lambda x: lbl_kws[x], func_var=pds3_keyword))

    return val_list