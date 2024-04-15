from collections import defaultdict
import os
import spiceypy as spice
from astropy.io import fits
import json
import numpy as np
import simpleeval

#adapted from Benjamin Sharkey's spiceypy code

class KwexSpice:
    abcorr = 'LT+S' #for now, this is a class variable and treated as a constant. we can make it an updateable property if we need to in the future.
    j2000_north = [0, 0, 1]

    spice_path = os.path.dirname(os.path.realpath(__file__))

    #imports a list of body-fixed reference frames keyed to target names for use in surface geometry calculations
    with open(os.path.join(spice_path, 'body_frames.json')) as f:
        body_frames = json.load(f)

    #imports a list of FITS keywords used for initializing SPICE. Current list is based on NH FITS keywords and may not be universal.
    with open(os.path.join(spice_path, 'fits_spice_kws.json')) as f:
        spice_kw = json.load(f)

    #imports a list of basis vectors and rotation for each instrument frame, used for calculating boresight RA/Dec and position angles
    with open(os.path.join(spice_path, 'instr_frame_params.json')) as f:
        instr_frame_params = json.load(f)

    def __init__(self, fits_file, kernel_file, ref_frame, spacecraft):
        #spiceypy gets weird if you're not in the kernel directory
        spice.kclear()
        cwd = os.getcwd()
        os.chdir(os.path.dirname(kernel_file))
        spice.furnsh(kernel_file)
        os.chdir(cwd)

        #get initial keywords from FITS file to initialize SPICE
        with fits.open(fits_file) as f:
            hdr = f[0].header

        sclk = hdr[KwexSpice.spice_kw['sclk']]
        spice_sc_id = hdr[KwexSpice.spice_kw['spice_sc_id']]
        self._et = spice.scs2e(spice_sc_id, sclk)

        self._instr_frame = hdr[KwexSpice.spice_kw['instr_frame']]
        spice_target_name = hdr[KwexSpice.spice_kw['spice_target_name']]
        fits_target_name = hdr[KwexSpice.spice_kw['fits_target_name']]

        self._spice_target_id, self.spice_target_name = self.get_spice_id(spice_target_name, fits_target_name)

        self._ref_frame = ref_frame
        self.spacecraft = spacecraft

        self._i2j_mat = None
        self._j2i_mat = None
        self._sol_pos = None
        self._target_pole_j2000_rec = None
        self._target_pole_img_coord = None
        self._north_img_coord = None

        #a default dictionary of empty state vectors of the form _state_dict[target_body][obs_body] so that once any particular state is calculated, it doesn't need to be recalculated
        self._state_dict = defaultdict(lambda: defaultdict(lambda: None))

        try:
            self.instr_basis_vector = KwexSpice.instr_frame_params[self._instr_frame]['basis_vector']
            self.tangent_coords = KwexSpice.instr_frame_params[self._instr_frame]['tan_coord']
            self.rot90 = KwexSpice.instr_frame_params[self._instr_frame]['rot90']
        except:
            self.instr_basis_vector = [0, 0, -1]
            self.tangent_coords = [1, 1, 0]
            self.rot90 = 0

    #fetch target spice ID from target spice name
    def get_spice_id(self, target, backup_target=None):
        try:
            stid = spice.bodn2c(target)
            stn = spice.bodc2n(stid)
        except spice.NotFoundError:
            #if name does not correspond to an ID (for example, because it's 'UNKNOWN', try a backup name)
            stid, stn = self.get_spice_id(backup_target)
        except:
            #if the spice lookup fails for some other reason, or if we're a level down and a backup target of None got plugged into the try, give up and just return None and the original target name
            stid = None
            stn = target
        
        return stid, stn

    #formulas that get reused are declared as properties with a gettr function that calculates the property the first time and simply returns it on subsequent calls
    @property
    def i2j_mat(self):
        if self._i2j_mat is None:
            try:
                self._i2j_mat = spice.pxform(self._instr_frame, self._ref_frame, self._et)
            except:
                pass
        return self._i2j_mat
    
    @property
    def j2i_mat(self):
        if self._j2i_mat is None:
            try:
                self._j2i_mat = spice.pxform(self._ref_frame, self._instr_frame, self._et)
            except:
                pass
        return self._j2i_mat
    
    @property
    def sol_pos(self):
        if self._sol_pos is None:
            try:
                self._sol_pos, _  = spice.spkpos('Sun', self._et, self._instr_frame, KwexSpice.abcorr, self.spacecraft)
            except:
                pass
        return self._sol_pos
    
    @property
    def target_pole_j2000_rec(self):
        if self._target_pole_j2000_rec is None:
            try:
                self._target_pole_j2000_rec = spice.radrec(1, *spice.bodeul(self._spice_target_id, self._et)[:2])
            except:
                #if the target doesn't have a defined pole, use this as a default
                self._target_pole_j2000_rec = [0, 0, 1]
        return self._target_pole_j2000_rec
    
    @property
    def target_pole_img_coord(self):
        if self._target_pole_img_coord is None:
            self._target_pole_img_coord = self.img_coord(self.target_pole_j2000_rec)
        return self._target_pole_img_coord
    
    @property
    def north_img_coord(self):
        if self._north_img_coord is None:
            self._north_img_coord = self.img_coord(KwexSpice.j2000_north)
        return self._north_img_coord
    
    def img_coord(self, j2000_coords):
        try:
            return spice.mxv(self.j2i_mat, j2000_coords)
        except:
            pass
    
    def atan(self, vector):
        new_vec = vector * self.tangent_coords
        tan_comps = new_vec[new_vec != 0]
        return np.arctan2(*tan_comps)
    
    #state function encapsulates the various target_state, geo_state, etc. variables used in previous version
    def state(self, target_body, obs_body):
        if self._state_dict[target_body][obs_body] is not None:
            return self._state_dict[target_body][obs_body]
        else:
            try:
                return spice.spkezr(target_body, self._et, self._ref_frame, KwexSpice.abcorr, obs_body)[0]
            except:
                pass

    def sol_phase_ang(self, target_body, obs_body):
        try:
            phase_angle = spice.phaseq(self._et, target_body, 'SUN', obs_body, KwexSpice.abcorr) * spice.dpr()
        except spice.SpiceBODIESNOTDISTINCT:
            #if the sun is one of the two arguments, spice.phaseq fails, so return an angle of 0 degrees in that case
            phase_angle = 0
        return phase_angle
    
    def sub_point(self, sc_or_solar, lon_or_lat):
        if sc_or_solar == 'sc':
            sub = spice.subpnt('NEAR POINT/ELLIPSOID', self.spice_target_name, self._et, KwexSpice.body_frames[self.spice_target_name], KwexSpice.abcorr, self.spacecraft)
        elif sc_or_solar == 'solar':
            sub = spice.subslr('NEAR POINT/ELLIPSOID', self.spice_target_name, self._et, KwexSpice.body_frames[self.spice_target_name], KwexSpice.abcorr, self.spacecraft)

        sub_lat = spice.reclat(sub[0])

        if lon_or_lat == 'lon':
            return (sub_lat[1] * spice.dpr()) % 360
        elif lon_or_lat == 'lat':
            return sub_lat[2] * spice.dpr()
        
def init_eval(ksp):
    se = simpleeval.SimpleEval()
    se.names['ksp'] = ksp
    se.names['i2j_mat'] = ksp.i2j_mat
    se.names['j2i_mat'] = ksp.j2i_mat
    se.names['sol_pos'] = ksp.sol_pos
    se.names['target_pole_j2000_rec'] = ksp.target_pole_j2000_rec
    se.names['target_pole_img_coord'] = ksp.target_pole_img_coord
    se.names['north_img_coord'] = ksp.north_img_coord
    se.names['target_name'] = ksp.spice_target_name
    se.names['minus_x_axis'] = [-1, 0, 0]
    se.names['j2000_north'] = [0, 0, 1]
    se.names['instr_basis_vector'] = ksp.instr_basis_vector
    se.names['rot90'] = ksp.rot90
    se.functions['recrad'] = spice.recrad
    se.functions['mxv'] = spice.mxv
    se.functions['dpr'] = spice.dpr
    se.functions['m2q'] = spice.m2q
    se.functions['vnorm'] = spice.vnorm

    return se
