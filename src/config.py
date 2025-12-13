from pathlib import Path
import json
from dataclasses import dataclass, field

from constants import *
from names import ConfigKey, ConfigState

current = None

DEFAULTS = {
    ConfigKey.LOGGING: False, #log basic runtime info, yes/no?
    ConfigKey.LOG_OUTPUT: 'tmp/kwex.log', #log to a file or 'console'
    ConfigKey.WARNING: ConfigState.ERROR, #treat warnings as errors, info, or messages sent to console
    ConfigKey.OUTPUT_CHECK: False, #check output for errors and compile list of bad output files, yes/no?
    ConfigKey.RECURSIVE_INPUT_DIR: False, #search all subdirectories for --input path/to/dir, yes/no?
    ConfigKey.FIND_PAIR: True, #find complementary input files, yes/no?
    ConfigKey.ALLOW_UNPAIRED: False, #allow products that are just one file (.lbl or .fits), yes/no? disabled by default because only file being present usually represents a problem
    ConfigKey.KEEP_JSON: False, #keep json files with stored keyword values after program run, yes/no?
    ConfigKey.VELOCITY: True, #activate velocity and produce output, yes/no? (no to just fill out json value files)
    ConfigKey.OUTPUT_EXT: '.lblx', #file extension for output files.
    ConfigKey.DATA_OUTPUT: ConfigState.IGNORE, #when producing output files, ignore data files, or move/copy to the output location.
    ConfigKey.SPICE_KERNEL: '', #file path for a spice kernel. no default because kernels are big.
    ConfigKey.SPICE_EQUATIONS: 'resources/spice_equations.json', #set of equations for calculating SPICE geometry kets to FITS keywords. likely mission-specific. default list is for NH, adapted from Benjamin Sharkey's spiceypy code.
    ConfigKey.SPICE_BODY_FRAMES: 'resources/body_frames.json', #lookup table of body-fixed reference frames for targets. default list is specific to NH targets.
    ConfigKey.SPICE_FITS_KWS: 'resources/fits_spice_kws.json', #lookup table of FITS keywords that encode informaion needed for SPICE calculattions. likely missiong-specific. default list is for NH.
    ConfigKey.SPICE_INSTR_FRAME_PARAMS: 'resources/instr_frame_params.json', #helper dictionary with parameters defining instrument reference frames for SPICE calculations. default list is specific to NH instruments.
    ConfigKey.SPICE_SPACECRAFT: 'NH', #NAIF ID of the spacecraft, used in SPICE calculations.
    ConfigKey.SPICE_INERTIAL_FRAME: 'J2000', #default inertial reference frame.
    ConfigKey.SPICE_ABCORR: 'LT+S' #SPICE setting for aberration corrections due to light travel time. LT+S corrects for "for one-way light time and stellar aberration using a Newtonian formulation."
}

@dataclass
class Config:
    """ Class for accessing and modifying config values. One instance is created at runtime and used across program. """
    values: dict = field(default_factory=lambda: DEFAULTS.copy())

    def load_user_file(self):
        """ Config class method that overrides default config values with those from user-stored file """
        if CONFIG_PATH.exists():
            user_config = json.loads(CONFIG_PATH.read_text())
            self.values.update(user_config)

    def apply_cli_overrides(self, overrides: dict):
        """ Config class method that overrides current config values with CLI overrides """
        for key, value in overrides.items():
            if value is not None:
                value = get_boolean(key, value)
                self.values[key] = value

    def save_config(self, key: str, value: str):
        """ Config class method that saves new values to user config file """
        if CONFIG_PATH.exists():
            user_config = json.loads(CONFIG_PATH.read_text())
        else:
            user_config = {}

        value = get_boolean(key, value)

        user_config[key] = value

        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(user_config, indent=4))

def get_config(key: str) -> str:
    """ Gettr function for config key values """
    return current.values[key]

def path(key: str) -> Path:
    """ Helper function that converts path-like config values into pathlib Paths """
    key_path = Path(get_config(key))
    if key_path.is_absolute():
        return key_path
    else:
        return KWEX_DIR / key_path
    
def get_boolean(key: str, value: str):
    """ Helper function that converts ENABLED/DISABLED strings to boolean values """
    if key in CONFIG_BOOLEAN:
        return CONFIG_ENABLED_DICT[value]
    else:
        return value