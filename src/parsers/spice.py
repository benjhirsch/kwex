import os
import spiceypy as spice
import json
from collections import defaultdict
import numpy as np

from constants import *
from config import get_config, path
from state import run_state
from names import SpiceKey, ConfigKey, Source
from utils.sources import check_kernel
from loggers.interrupter import error_handler, warning_handler
from loggers.logger import get_logger
from utils.values import add_to_val, init_eval

class SpiceWrapper:
    """ Wrapper class for spiceypy functions that creates an object with properties to a specific data product (e.g. ephemeris, instrument frame, target id, etc.) """
    body_frames = json.loads(path(ConfigKey.SPICE_BODY_FRAMES).read_text())
    fits_spice_kws = json.loads(path(ConfigKey.SPICE_FITS_KWS).read_text())
    instr_frame_params = json.loads(path(ConfigKey.SPICE_INSTR_FRAME_PARAMS).read_text())
    abcorr = get_config(ConfigKey.SPICE_ABCORR)

    def __init__(self, fits_kws: dict):
        self._fits_kws = fits_kws
        sclk = self._get_fits_kw(SpiceKey.SPACECRAFT_CLOCK)
        spice_sc_id = self._get_fits_kw(SpiceKey.SPACECRAFT_ID)
        self._et = spice.scs2e(spice_sc_id, sclk)

        self._instr_frame = self._get_fits_kw(SpiceKey.INSTRUMENT_FRAME)
        spice_target_name = self._get_fits_kw(SpiceKey.SPICE_TARGET_NAME)
        fits_target_name = self._get_fits_kw(SpiceKey.FITS_TARGET_NAME)

        self._spice_target_id, self.spice_target_name = self._get_spice_id(spice_target_name, fits_target_name)
        self._ref_frame = get_config(ConfigKey.SPICE_INERTIAL_FRAME)
        self.spacecraft = get_config(ConfigKey.SPICE_SPACECRAFT)

        self._i2j_mat = None
        self._j2i_mat = None
        self._sol_pos = None
        self._target_pole_inertial_frame_rec = None
        self._target_pole_img_coord = None
        self._north_img_coord = None

        self._state_dict = defaultdict(lambda: defaultdict(lambda: None))

        try:
            self._boresight_basis_vector = np.array(SpiceWrapper.instr_frame_params[self._instr_frame][SpiceKey.BORESIGHT_BASIS_VECTOR])
            self._instr_uv_plane = SpiceWrapper.instr_frame_params[self._instr_frame][SpiceKey.INSTR_UV_PLANE]
        except:
            warning_handler(f'Invalid instrument frame {self._instr_frame}.')
            self._boresight_basis_vector = np.array([0, 0, -1])
            self._instr_uv_plane = ['+u', '+v', '']

    def _get_fits_kw(self, keyword):
        """ SpiceWrapper helper method that retrieves a FITS keyword value corresponding to a quantity necessary for spice computations """
        try:
            return self._fits_kws[SpiceWrapper.fits_spice_kws[keyword]]
        except:
            warning_handler(f'{keyword} not found.')

    def _get_spice_id(self, target: str, backup_target=None) -> tuple[str, str]:
        """ SpiceWrapper method that retrieves target spice ID from target spice name. """
        try:
            stid = spice.bodn2c(target)
            stn = spice.bodc2n(stid)
        except spice.NotFoundError:
            #if name does not correspond to an ID (for example, because it's 'UNKNOWN', try a backup name)
            stid, stn = self._get_spice_id(backup_target)
        except:
            #if the spice lookup fails for some other reason, or if we're a level down and a backup target of None got plugged into the try, give up and just return None and the original target name
            stid = None
            stn = target

        return stid, stn
    
    #formulas that get reused are declared as properties with a gettr function that calculates the property the first time and simply returns it on subsequent calls
    @property
    def i2j_mat(self) -> np.ndarray:
        """ SpiceWrapper property that calculates and returns matrix for converting instrument position vectors to some inertial reference frame's position vectors. """
        if self._i2j_mat is None:
            try:
                self._i2j_mat = spice.pxform(self._instr_frame, self._ref_frame, self._et)
            except:
                pass
        return self._i2j_mat
    
    @property
    def j2i_mat(self) -> np.ndarray:
        """ SpiceWrapper property that calculates and returns matrix for converting some inertial reference frame's position vectors to instrument position vectors. """
        if self._j2i_mat is None:
            try:
                self._j2i_mat = spice.pxform(self._ref_frame, self._instr_frame, self._et)
            except:
                pass
        return self._j2i_mat
    
    @property
    def sol_pos(self) -> tuple:
        """ SpiceWrapper property that calculates and returns spacecraft position relative to the Sun. """
        if self._sol_pos is None:
            try:
                self._sol_pos, _  = spice.spkpos('Sun', self._et, self._instr_frame, SpiceWrapper.abcorr, self.spacecraft)
            except:
                pass
        return self._sol_pos
    
    @property
    def target_pole_inertial_frame_rec(self) -> np.ndarray:
        """ SpiceWrapper property that calculates and returns inertial frame rectangular coordinates of target pole. """
        if self._target_pole_inertial_frame_rec is None:
            try:
                self._target_pole_inertial_frame_rec = spice.radrec(1, *spice.bodeul(self._spice_target_id, self._et)[:2])
            except:
                #if the target doesn't have a defined pole, use this as a default
                self._target_pole_inertial_frame_rec = INERTIAL_FRAME_NORTH
        return self._target_pole_inertial_frame_rec
    
    @property
    def target_pole_img_coord(self) -> np.ndarray:
        """ SpiceWrapper property that calculates and returns rectangular inertial frame coordinates of target pole in terms of the instrument's frame. """
        if self._target_pole_img_coord is None:
            self._target_pole_img_coord = self._img_coord(self.target_pole_inertial_frame_rec)
        return self._target_pole_img_coord
    
    @property
    def north_img_coord(self) -> np.ndarray:
        """ SpiceWrapper property that calculates and returns rectangular coordinates of inertial reference frame north in terms of the instrument's frame. """
        if self._north_img_coord is None:
            self._north_img_coord = self._img_coord(INERTIAL_FRAME_NORTH)
        return self._north_img_coord
    
    def _img_coord(self, inertial_frame_coords: np.ndarray) -> np.ndarray:
        """ SpiceWrapper helper method that performs matrix multiplication to get a set of inertial reference frame rectangular coordinates in terms of the instrument's frame. """
        try:
            return spice.mxv(self.j2i_mat, inertial_frame_coords)
        except:
            pass

    def quaternion_component(self, matrix, component):
        """ SpiceWrapper method that computes quaternion of transformation matrix and returns a component of it (a, x, y, z) """
        comp_dict = {'a': 0, 'x': 1, 'y': 2, 'z': 3}
        return spice.m2q(matrix)[comp_dict[component.lower()]]

    def clock_angle(self, vector: np.ndarray) -> np.ndarray:
        """ SpiceWrapper method that projects a 3D vector from the instrument's reference frame onto the instrument's image plane, then calculates the clock angle of that vector. """
        #identifies which instrument frame axes correspond to horizontal (u) and vertical (v) axes on the image plane
        comp_idx = tuple([i in comp for comp in self._instr_uv_plane].index(True) for i in ['v', 'u'])
        #gets the component values of the vector for those axes and flips sign if necessary
        comp_vals = tuple([vector[i] * (-1)**(self._instr_uv_plane[i].startswith('-')) for i in comp_idx])
        return np.arctan2(*comp_vals) * spice.dpr() % 360
    
    def instrument_position_angle(self, axis: str) -> float:
        """ SpiceWrapper method that calculates instrument position angle """
        axis_rot_dict = {'+x': -90, '+y': 0, '+z': -270}
        try:
            return (self.clock_angle(self.north_img_coord) + axis_rot_dict[axis.lower()]) % 360
        except:
            warning_handler(f'Invalid position angle axis {axis}.')
    
    def state_vector_component(self, from_body: str, to_body: str, vector: str, component: str) -> float:
        """ SpiceWrapper method that returns value stored in _state_dict or calculates vector from 'from_body' to 'to_body' in selected inertial reference frame. 'vector' takes 'position' or 'velocity'. 'component' takes 'x', 'y', or 'z'. """ 
        vector_dict = {'position': 0, 'velocity': 3}
        component_dict = {'x': 0, 'y': 1, 'z': 2}
        try:
            state_idx = vector_dict[vector.lower()] + component_dict[component.lower()]
        except KeyError:
            warning_handler('Invalid vector name or component.')

        if self._state_dict[from_body][to_body] is None:
            try:
                self._state_dict[from_body][to_body] = spice.spkezr(from_body, self._et, self._ref_frame, SpiceWrapper.abcorr, to_body)[0]
            except:
                return
            
        return self._state_dict[from_body][to_body][state_idx]
    
    def state_vector_magnitude(self, from_body: str, to_body: str, vector: str) -> float:
        """ SpiceWrapper method that computes vnorm of the three components of a state_vector_component vector """
        return spice.vnorm([self.state_vector_component(from_body, to_body, vector, i) for i in ['x', 'y', 'z']])
    
    def sol_phase_ang(self, target_body: str, obs_body: str) -> float:
        """ SpiceWrapper method that calculates solar phase angle in radians between target body and observer. """
        try:
            phase_angle = spice.phaseq(self._et, target_body, 'SUN', obs_body, SpiceWrapper.abcorr) * spice.dpr()
        except spice.SpiceBODIESNOTDISTINCT:
            #if the sun is one of the two arguments, spice.phaseq fails, so return an angle of 0 degrees in that case
            phase_angle = 0
        return phase_angle
    
    def sub_point(self, sc_or_solar: str, lon_or_lat: str) -> float:
        """ SpiceWrapper method that calculates longitude or latitude in degrees of a subsolar or subspacecraft point on the surface of a target body. """
        try:
            if sc_or_solar.lower() == 'sc':
                sub = spice.subpnt('NEAR POINT/ELLIPSOID', self.spice_target_name, self._et, SpiceWrapper.body_frames[self.spice_target_name], SpiceWrapper.abcorr, self.spacecraft)
            elif sc_or_solar.lower() == 'solar':
                sub = spice.subslr('NEAR POINT/ELLIPSOID', self.spice_target_name, self._et, SpiceWrapper.body_frames[self.spice_target_name], SpiceWrapper.abcorr, self.spacecraft)
        except spice.SpiceNOFRAME:
            warning_handler(f'No valid body-fixed frame found for {self.spice_target_name}.')
            return

        sub_lat = spice.reclat(sub[0])

        if lon_or_lat.lower() == 'lon':
            return (sub_lat[1] * spice.dpr()) % 360
        elif lon_or_lat.lower() == 'lat':
            return sub_lat[2] * spice.dpr()
        
    def instrument_boresight(self, ra_or_dec: str) -> float:
        """ SpiceWrapper method that calculates instrument boresight coordinates in selected inertial reference frame. Argument 'ra_or_dec' takes either 'ra' or 'dec' and determines which value is returned. """
        coord_dict = {'ra': 1, 'dec': 2}
        try:
            coord_idx = coord_dict[ra_or_dec.lower()]
        except KeyError:
            warning_handler(f'Invalid coordinate name {ra_or_dec}')
            return
        
        radec = spice.recrad(spice.mxv(self.i2j_mat, self._boresight_basis_vector))[coord_idx]

        return radec * spice.dpr()
    
def init_spice(var_list):
    """ Function to load SPICE kernels for SPICE calculations. """
    if len(var_list[Source.SPICE]) > 0:
        check_kernel(path(ConfigKey.SPICE_KERNEL))
        kernel = path(ConfigKey.SPICE_KERNEL)
        error_handler(lambda: kernel.is_file(), 'No SPICE kernel specified.')
        spice.kclear()
        
        if kernel.suffix == '.tm':
            #spiceypy gets weird if you're not in the kernel directory
            cwd = os.getcwd()
            os.chdir(kernel.parent)
            spice.furnsh(kernel.as_posix())
            os.chdir(cwd)
        else:
            spice.furnsh(kernel.as_posix())

        spice_eq_path = path(ConfigKey.SPICE_EQUATIONS)
        with spice_eq_path.open() as f:
            eq_list = json.load(f)
        run_state.spice_eqns = eq_list

def get_spice_values(var_list: dict, fits_kws: dict, spice_eqs: dict) -> Path:
    """ Function that calculates SPICE geometry values corresponding to Velocity template variables. Uses a spiceypy wrapper and the simpeleeval library to calculate values. """
    get_logger().info('Calculating SPICE keywords...')
    val_list = defaultdict(lambda: {})

    #simpleeval evaluator translates str formulations of spice functions into something evaluable
    if len(var_list[Source.SPICE]) > 0:
        try:
            ksp = SpiceWrapper(fits_kws[0])
        except:
            warning_handler(f'Unable to find FITS keywords necessary for SPICE calculations.')
            return

        evaluator = init_eval(ksp)

    for keyword in var_list[Source.SPICE]:
        val_list = add_to_val(val_list, Source.SPICE, keyword, val_func=lambda x: evaluator.eval(spice_eqs[x]), except_val='KEYWORD NOT RECALCULATED')

    return val_list

def get_equations() -> dict:
    """ Parser that loads a dictionary of SPICE equations evaluable by SimpleEval. """
    spice_eqs = path(ConfigKey.SPICE_EQUATIONS)
    with spice_eqs.open() as f:
        eq_list = json.load(f)

    #removes namespaces from numpy and spice functions because otherwise they don't work with simpleeval
    for eq in eq_list:
        eq_list[eq] = eq_list[eq].replace('np.', '').replace('spice.', '')

    return eq_list
