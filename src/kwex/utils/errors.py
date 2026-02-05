from ..loggers import *
from ..config import get_config
from ..constants import *
from ..names import ConfigKey, ConfigState
from ..state import run_state

class KwexError(Exception):
    def __init__(self, message):
        self.message = message

BAD_OUT = {
    'Unresolved template pointers': [
        '$label',
        '$fits',
        '$spice',
        '${label',
        '${fits',
        '${spice'
    ],
    'Unresolved Velocity logic': [
        '#if',
        '#for',
        '#set',
        '#parse'
    ],
    'Unrecorded keyword values': [
        'KEYWORD NOT FOUND',
        'KEYWORD NOT RECALCULATED'
    ]
}

def error_handler(test, message: str, *madlibs: str):
    """ Logging utility for handling error messages and ending program. 'test' is a conditional that evaluates to true or false as a lambda function. If false, message is logged and program ends."""
    if not test():
        #if false, end program and say why
        raise KwexError(message % madlibs)

def warning_handler(message: str, *madlibs: str):
    """ Logging utility for handling warning level logs depending on user configuraion.\n
    ERROR: treat warnings as errors.\n
    CONSOLE: treat warnings as normal messages but always send them to console.\n
    INFO: treat warnings as info logging messages. """
    if get_config(ConfigKey.WARNING) == ConfigState.ERROR:
        #treat warnings as errors
        error_handler(lambda: False, message % madlibs)
    elif get_config(ConfigKey.WARNING) == ConfigState.CONSOLE:
        #send warnings to console, but don't end program
        logger.get_logger().warning(message % madlibs)
    else:
        #treat warnings the same as any info logging message
        logger.get_logger().info(message % madlibs)

def log_bad_output():
    """ Logging utility that lists output files with bad output (unparsed Velocity code, keywords with missing values) """
    if get_config(ConfigKey.OUTPUT_CHECK):
        any_bad = False
        
        logger.info_logger('Checking output for errors')
        BAD_OUT['Unresolved local variables'] = run_state.local_template_vars
        
        for file in run_state.output_list:
            bad_found = {b: False for b in BAD_OUT.keys()}
            
            if file in run_state.bad_output_list:
                logger.info_logger('Unrecorded keyword values: %s', file.as_posix())
                any_bad = True
            
            if ConfigKey.VELOCITY:
                try:
                    with file.open() as f:
                        for line in f:
                            if all(bad_found.values()):
                                break
                            
                            for bad in BAD_OUT.keys():
                                if not bad_found[bad] and any(bad in line for bad in BAD_OUT[bad]):
                                    logger.info_logger('%s: %s', bad, file.as_posix())
                                    bad_found[bad] = True
                                    any_bad = True
                except:
                    warning_handler('Invalid output file %s', file.as_posix())

        if not any_bad:
            logger.info_logger('No errors found')
