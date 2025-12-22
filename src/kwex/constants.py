from pathlib import Path
from .names import ConfigKey, ConfigState, Source

KWEX_DIR = Path(__file__).resolve().parent
VALS_DIR = KWEX_DIR / 'tmp'
JAVA_DIR = KWEX_DIR / 'velocity/java'
RESOURCE_DIR = KWEX_DIR / 'resources'
CONFIG_PATH = Path.home() / '.kwex/config/config.json'

JAVA_SOURCE = JAVA_DIR / 'VMtoXML.java'
JAVA_CLASS = JAVA_DIR / 'VMtoXML.class'

JAR_FILES = ['.',
             'velocity-1.7.jar',
             'velocity-tools-2.0.jar',
             'jackson-core-2.9.9.jar',
             'jackson-databind-2.9.9.jar',
             'jackson-annotations-2.9.9.jar',
             'commons-collections-3.2.2.jar',
             'commons-lang-2.4.jar']

VAR_SUB_LIST = RESOURCE_DIR / 'var_sub.json'
MAJOR_TO_VERSION = RESOURCE_DIR / 'major_to_version.json'

RESERVED_XML_CHARS = {
    '&': 'amp',
    '<': 'lt',
    '>': 'gt'
}

EXTENSIONS = {
    Source.PDS3: ['.lbl'],
    Source.FITS: ['.fit', '.fits']
}

INERTIAL_FRAME_NORTH = [0, 0, 1]

CONFIG_ENABLED_DICT = {
    ConfigState.ENABLED: True,
    ConfigState.DISABLED: False
}

CONFIG_BOOLEAN = [
    ConfigKey.LOGGING,
    ConfigKey.OUTPUT_CHECK,
    ConfigKey.RECURSIVE_INPUT_DIR,
    ConfigKey.FIND_PAIR,
    ConfigKey.ALLOW_UNPAIRED,
    ConfigKey.KEEP_JSON,
    ConfigKey.VELOCITY
]

CONFIG_STATES = {
    ConfigKey.WARNING: [
        ConfigState.ERROR,
        ConfigState.CONSOLE,
        ConfigState.INFO
    ],
    ConfigKey.DATA_OUTPUT: [
        ConfigState.IGNORE,
        ConfigState.COPY,
        ConfigState.MOVE
    ]
}

BAD_OUTPUT_CHECK = [
    '$label',
    '$fits',
    '$spice',
    '${label',
    '${fits',
    '${spice',
    '#if',
    '#for',
    '#set',
    '#parse',
    'KEYWORD VALUE NOT FOUND',
    'KEYWORD NOT RECALCULATED'
]