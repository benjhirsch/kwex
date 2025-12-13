from enum import StrEnum

class ConfigKey(StrEnum):
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
    SPACECRAFT_CLOCK = 'sclk'
    SPACECRAFT_ID = 'spice_sc_id'
    INSTRUMENT_FRAME = 'instr_frame'
    SPICE_TARGET_NAME = 'spice_target_name'
    FITS_TARGET_NAME = 'fits_target_name'
    BORESIGHT_BASIS_VECTOR = 'boresight_basis_vector'
    INSTR_UV_PLANE = 'instr_uv_plane'

class Source(StrEnum):
    PDS3 = 'pds3'
    FITS = 'fits'
    SPICE = 'spice'
