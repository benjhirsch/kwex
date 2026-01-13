from enum import StrEnum, Enum, auto

class ConfigKey(StrEnum):
    """ Symbolic names for configuration keys with string values for use in JSON config file. """
    LOGGING = 'logging'
    LOG_OUTPUT = 'log_output'
    WARNING = 'warning_output'
    OUTPUT_CHECK = 'output_check'
    RECURSIVE_INPUT_DIR = 'recursive_input_dir'
    FIND_PAIR = 'find_input_pair'
    ALLOW_UNPAIRED = 'allow_unpaired'
    KEEP_JSON = 'keep_json'
    VELOCITY = 'activate_velocity'
    OUTPUT_EXT = 'output_ext'
    DATA_OUTPUT = 'data_output'

    SPICE_KERNEL = 'spice_kernel'
    SPICE_EQUATIONS = 'spice_equations'
    SPICE_BODY_FRAMES = 'body_frames'
    SPICE_FITS_KWS = 'spice_fits_kws'
    SPICE_INSTR_FRAME_PARAMS = 'instr_frame_params'
    SPICE_SPACECRAFT = 'spice_spacecraft'
    SPICE_INERTIAL_FRAME = 'spice_frame'
    SPICE_ABCORR = 'abcorr'

class ConfigState(StrEnum):
    """ Symbolic names for configuration key values with string values for use in JSON config file. """
    ENABLED = 'ENABLED'
    DISABLED = 'DISABLED'
    ERROR = 'ERROR'
    CONSOLE = 'CONSOLE'
    BLANK = 'BLANK'
    INFO = 'INFO'
    IGNORE = 'IGNORE'
    COPY = 'COPY'
    MOVE = 'MOVE'

class SpiceKey(StrEnum):
    """ Symbolic names for keys that map to components needed for SPICE computations. """
    SPACECRAFT_CLOCK = 'sclk'
    SPACECRAFT_ID = 'spice_sc_id'
    INSTRUMENT_FRAME = 'instr_frame'
    SPICE_TARGET_NAME = 'spice_target_name'
    FITS_TARGET_NAME = 'fits_target_name'
    BORESIGHT_BASIS_VECTOR = 'boresight_basis_vector'
    INSTR_UV_PLANE = 'instr_uv_plane'

class Source(StrEnum):
    """ Symbolic names for input source file types. """
    PDS3 = 'label'
    FITS = 'fits'
    SPICE = 'spice'

class PointerFlag(StrEnum):
    """ Symbolic names for Velocity template pointer flags with string values to use in the templates. """
    UNIT = 'unit'
    ITERATE = 'iterate'
    FILEINFO = 'fileinfo'

class FITS(Enum):
    HEADER = auto()
    EXT_NUM = auto()
    KEYWORD = auto()
    TREE = auto()

class PDS3(StrEnum):
    VALUE = 'value'
    UNIT = 'unit'
    OBJECT = 'OBJECT'
    END_OBJECT = 'END_OBJECT'
    FLAT = auto()
    TEMPLATE_KW = auto()
