from collections import defaultdict
import os
import spiceypy as spice
from astropy.io import fits
import json

class KwexSpice:
    abcorr = 'LT+S'
    
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'body_frames.json')) as f:
        body_frames = json.load(f)

    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fits_spice_kws.json')) as f:
        spice_kw = json.load(f)

    def __init__(self, fits_file, kernel_file, ref_frame, spacecraft):
        spice.kclear()
        cwd = os.getcwd()
        os.chdir(os.path.dirname(kernel_file))
        spice.furnsh(kernel_file)
        os.chdir(cwd)

        with fits.open(fits_file) as f:
            hdr = f[0].header

        sclk = hdr[KwexSpice.spice_kw['sclk']]
        spice_sc_id = hdr[KwexSpice.spice_kw['spice_sc_id']]
        self._et = spice.scs2e(spice_sc_id, sclk)

        self._instr_frame = hdr[KwexSpice.spice_kw['instr_frame']]
        self.spice_target_name = hdr[KwexSpice.spice_kw['spice_target_name']]
        try:
            self._spice_target_id = spice.bodn2c(self.spice_target_name)
            self.spice_target_name = spice.bodc2n(self._spice_target_id)
        except:
            self._spice_target_id = None
        
        self._ref_frame = ref_frame
        self.spacecraft = spacecraft

        self._i2j_mat = None
        self._j2i_mat = None
        self._sol_pos = None
        self._target_pole_j2000_rec = None

        self._state_dict = defaultdict(lambda: defaultdict(lambda: None))

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
                self._target_pole_j2000_rec = [0, 0, 1]
        return self._target_pole_j2000_rec

    def state(self, target_body, obs_body):
        if self._state_dict[target_body][obs_body] is not None:
            return self._state_dict[target_body][obs_body]
        else:
            try:
                return spice.spkezr(target_body, self._et, self._ref_frame, KwexSpice.abcorr, obs_body)[0]
            except:
                pass

    def sol_phase_ang(self, target_body, obs_body):
        return spice.phaseq(self._et, target_body, 'SUN', obs_body, KwexSpice.abcorr) * spice.dpr()
    
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