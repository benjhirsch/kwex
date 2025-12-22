import sys

from . import logger
from ..config import get_config
from ..constants import *
from ..names import ConfigKey, ConfigState
from ..state import run_state

def error_handler(test, message: str):
    """ Logging utility for handling error messages and ending program. 'test' is a conditional that evaluates to true or false as a lambda function. If false, message is logged and program ends."""
    if not test():
        #if false, end program and say why
        logger.get_logger().error(message)
        sys.exit()

def warning_handler(message: str):
    """ Logging utility for handling warning level logs depending on user configuraion.\n
    ERROR: treat warnings as errors.\n
    CONSOLE: treat warnings as normal messages but always send them to console.\n
    INFO: treat warnings as info logging messages. """
    if get_config(ConfigKey.WARNING) == ConfigState.ERROR:
        #treat warnings as errors
        error_handler(lambda: False, message)
    elif get_config(ConfigKey.WARNING) == ConfigState.CONSOLE:
        #send warnings to console, but don't end program
        logger.get_logger().warning(message)
    else:
        #treat warnings the same as any info logging message
        logger.get_logger().info(message)

def log_bad_output():
    """ Logging utility that lists output files with bad output (unparsed Velocity code, keywords with missing values) """
    if get_config(ConfigKey.OUTPUT_CHECK):
        for file in run_state.output_list:
            bad = False
            if file in run_state.bad_output_list:
                bad = True
            
            if ConfigKey.VELOCITY:
                output_text = file.read_text()
                
                for bad_txt in BAD_OUTPUT_CHECK:
                    if bad_txt in output_text:
                        bad = True
                        continue
            if bad:
                logger.get_logger().info(f'BAD OUTPUT: {file.as_posix()}')
