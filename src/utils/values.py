import json
import simpleeval
import spiceypy as spice
import numpy as np

from loggers.logger import get_logger
from loggers.interrupter import warning_handler
from constants import *
from config import get_config
from state import run_state
from names import ConfigKey

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
        if get_config(ConfigKey.OUTPUT_CHECK):
            run_state.bad_output = True
        warning_handler(f'keyword {keyword} value not found because {e}')

    val_entry[keyword] = val

    return val_entry

def send_values(val_list: dict, output_path: Path) -> Path:
    """ Helper function that writes temporary *.json file to feed into Velocity engine """
    VALS_DIR.mkdir(parents=True, exist_ok=True)
    json_vals = VALS_DIR / f'vals_{output_path.with_suffix(".json").name}'

    get_logger().info(f'Recording keyword values in {json_vals.name}...')

    json_vals.write_text(json.dumps(val_list, indent=4))
    return json_vals

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