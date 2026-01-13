import json
import simpleeval
import spiceypy as spice
import numpy as np
import re

from ..loggers import *
from ..constants import *
from ..state import run_state

RESERVED_PATTERNS = []
for c in RESERVED_XML_CHARS:
    pattern = re.compile(r'\%s(?!.*;)' % c) #reserved character not followed by 0+ other characters and then a semi-colon
    escape_char = RESERVED_XML_CHARS[c]
    RESERVED_PATTERNS.append(tuple([pattern, escape_char]))

def add_to_val(keyword: str, val_func, func_var=None, except_val='KEYWORD VALUE NOT FOUND') -> dict:
    val_entry = {}
    """ Utility that constructs a dictionary of values retrieved from input files corresponding to variable pointers in a template file. """
    if not func_var:
        #if no explicit function variable is given, use keyword
        func_var = keyword
    try:
        val = val_func(func_var)
    except Exception as e:
        val = except_val
        run_state.bad_output = True
        warning_handler('keyword %s value not found because %s', keyword, e)

    val_entry[keyword] = val

    return val_entry

def send_values(val_list: dict, output_path: Path) -> Path:
    """ Helper function that writes temporary *.json file to feed into Velocity engine """
    json_vals = output_path.with_stem(f'vals_{output_path.stem}').with_suffix('.json')
    info_logger('Recording keyword values in %s', json_vals.name)
    val_list_str = fix_json(val_list)
    json_vals.write_text(val_list_str)

    return json_vals

def fix_json(val_list: dict):
    val_list_str = json.dumps(val_list, indent=4)
    #reserved XML character replacement
    for pattern, escape_char in RESERVED_PATTERNS:
        val_list_str = re.sub(pattern, escape_char, val_list_str)
    return val_list_str

def init_eval(ksp) -> simpleeval.SimpleEval:
    """ Funtion to initialize the simpleeval evaluator with values from a product's SpiceWrapper object. """
    evaluator = simpleeval.SimpleEval()
    
    #SpiceWrapper properties used as variables in the methods below
    evaluator.names['ksp'] = ksp
    evaluator.names['north_img_coord'] = ksp.north_img_coord
    evaluator.names['sol_pos'] = ksp.sol_pos
    evaluator.names['i2j_mat'] = ksp.i2j_mat
    evaluator.names['j2i_mat'] = ksp.j2i_mat
    evaluator.names['spacecraft'] = ksp.spacecraft
    evaluator.names['target_name'] = ksp.spice_target_name
    evaluator.names['target_pole_img_coord'] = ksp.target_pole_img_coord
    evaluator.names['target_pole_inertial_frame_rec'] = ksp.target_pole_inertial_frame_rec

    #high-level SpiceWrapper methods for computing final attribute values
    evaluator.functions['instrument_boresight'] = ksp.instrument_boresight
    evaluator.functions['clock_angle'] = ksp.clock_angle
    evaluator.functions['quaternion_component'] = ksp.quaternion_component
    evaluator.functions['state_vector_magnitude'] = ksp.state_vector_magnitude
    evaluator.functions['state_vector_component'] = ksp.state_vector_component
    evaluator.functions['instrument_position_angle'] = ksp.instrument_position_angle
    evaluator.functions['sub_point'] = ksp.sub_point
    evaluator.functions['sol_phase_ang'] = ksp.sol_phase_ang
    
    #low-level spicepy and numpy functions used in the above methods for those who want to get creative
    evaluator.functions['recrad'] = spice.recrad
    evaluator.functions['mxv'] = spice.mxv
    evaluator.functions['dpr'] = spice.dpr
    evaluator.functions['m2q'] = spice.m2q
    evaluator.functions['vnorm'] = spice.vnorm
    evaluator.functions['pxform'] = spice.pxform
    evaluator.functions['spkpos'] = spice.spkpos
    evaluator.functions['radrec'] = spice.radrec
    evaluator.functions['bodeul'] = spice.bodeul
    evaluator.functions['dpr'] = spice.dpr
    evaluator.functions['spkezr'] = spice.spkezr
    evaluator.functions['phaseq'] = spice.phaseq
    evaluator.functions['subpnt'] = spice.subpnt
    evaluator.functions['subslr'] = spice.subslr
    evaluator.functions['reclat'] = spice.reclat
    evaluator.functions['array'] = np.array
    evaluator.functions['ndarray'] = np.ndarray
    evaluator.functions['arctan2'] = np.arctan2

    return evaluator
