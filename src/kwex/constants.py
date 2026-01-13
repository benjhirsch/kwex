from pathlib import Path
from importlib.resources import files

from .names import ConfigKey, ConfigState, Source

KWEX_DIR = Path(__file__).resolve().parent
USER_DIR = Path.home() / '.kwex'
CONFIG_PATH = USER_DIR / 'config.json'

RESOURCE_PATH = files('kwex.resources')
VAR_SUB_JSON = RESOURCE_PATH.joinpath('pds3/var_sub.json')
MAJOR_TO_VERSION = RESOURCE_PATH.joinpath('java/major_to_version.json')
JAVA_SOURCE = RESOURCE_PATH.joinpath('java/VMtoXML.java')

JAVA_DIR = KWEX_DIR / 'resources/java'
JAVA_CLASS = USER_DIR / 'VMtoXML.class'
JAR_FILES = ['velocity-1.7.jar',
             'velocity-tools-2.0.jar',
             'jackson-core-2.9.9.jar',
             'jackson-databind-2.9.9.jar',
             'jackson-annotations-2.9.9.jar',
             'commons-collections-3.2.2.jar',
             'commons-lang-2.4.jar']

RESERVED_XML_CHARS = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;'
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
