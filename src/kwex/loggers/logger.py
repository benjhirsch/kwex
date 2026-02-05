import logging

from ..config import get_config, path
from ..names import ConfigKey, ConfigState

class LevelBasedFormatter(logging.Formatter):
    """ Custom logging formatter class that changes log output based on the level (info, warning, error) """
    def __init__(self, log_to_file=False):
        self.log_to_file = log_to_file

    FORMATS = {
        logging.INFO: '%(message)s',
        logging.WARNING: 'Issue: %(message)s',
        logging.ERROR: 'Error: %(message)s\nkwex exited without finishing'
    }

    def format(self, record):
        level = record.levelno
        if level == logging.WARNING:
            level = {ConfigState.ERROR: logging.ERROR, ConfigState.CONSOLE: logging.WARNING, ConfigState.INFO: logging.INFO}[get_config(ConfigKey.WARNING)]

        if self.log_to_file:
            #for logs send to file, append a timestamp
            fmt = '%(asctime)s.%(msecs)03d: ' + self.FORMATS[level]
            datefmt = '%Y-%m-%d %H:%M:%S'
            formatter = logging.Formatter(fmt, datefmt=datefmt)
        else:
            if level == logging.INFO:
                fmt = self.FORMATS[level] + '...'
            else:
                fmt = self.FORMATS[level]
            formatter = logging.Formatter(fmt=fmt)

        return formatter.format(record)
    
_startup_formatter = logging.Formatter(fmt='Error: %(message)s\nkwex exited without finishing')
    
_LOG_INITIALIZED = False

logger = logging.getLogger('kwex')
logger.setLevel(logging.DEBUG)
logger.propagate = False
#we need a basic error handler initialized before command line arguments (which may change log settings) are evaluated
startup_handler = logging.StreamHandler()
startup_handler.setFormatter(_startup_formatter)
startup_handler.setLevel(logging.WARNING)
logger.addHandler(startup_handler)

def init_log():
    """ Function to initialize logging object based on user configuration. Determines whether logging occurs, log formatting, and log output destination. """
    global _LOG_INITIALIZED
    if _LOG_INITIALIZED:
        return
    _LOG_INITIALIZED = True

    #get rid of th startup handler
    logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(LevelBasedFormatter())

    if get_config(ConfigKey.LOGGING) and get_config(ConfigKey.LOG_OUTPUT) == ConfigState.CONSOLE:
        #if info logs go to console, everything goes to console
        console_handler.setLevel(logging.INFO)
    elif get_config(ConfigKey.WARNING) == ConfigState.INFO:
        #if warnings are treated as info and info isn't going to console, only errors do
        console_handler.setLevel(logging.ERROR)
    else:
        #otherwise, if warnings aren't treated as info, send warnings and errors to console
        console_handler.setLevel(logging.WARNING)
    
    logger.addHandler(console_handler)

    if get_config(ConfigKey.LOGGING) and not get_config(ConfigKey.LOG_OUTPUT) == ConfigState.CONSOLE:
        #if info logs go to file, everything goes to file
        log_path = path(ConfigKey.LOG_OUTPUT)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, mode='w')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(LevelBasedFormatter(log_to_file=True))
        logger.addHandler(file_handler)

def get_logger() -> logging.getLogger:
    """ Gettr function for accessing the configured logging object """
    return logging.getLogger('kwex')

def info_logger(message: str, *madlibs: str):
    get_logger().info(message % madlibs)
