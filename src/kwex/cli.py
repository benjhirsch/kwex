import argparse
import sys
from pathlib import Path

from . import config
from .names import ConfigKey, ConfigState
from .constants import *
from .loggers import *

cfg = config.Config()

def cli_override(override: list, log: str) -> dict:
    """CLI function that returns a dictionary of custom configuration values to be used during script execution. """
    override_dict = {}
    
    if override:
        #config overrides from explicit command line
        for o in override:
            key, value = config_checker(o)
            override_dict[key] = value

    if log:
        #config overrides from command line logging arguments
        override_dict[ConfigKey.LOGGING] = ConfigState.ENABLED
        if log == ConfigState.CONSOLE:
            override_dict[ConfigKey.LOG_OUTPUT] = ConfigState.CONSOLE
        elif not log == ConfigState.BLANK:
            if Path(value).is_dir():
                value = Path(value).expanduser().resolve().as_posix()
            override_dict[ConfigKey.LOG_OUTPUT] = log

    return override_dict

def config_checker(config_arg: str) -> tuple[str, str]:
    """ CLI function that converts argument into keyword:value pair and checks for validity. """
    #some config settings have a limited set of acceptable values, defined in CONFIG_STATES
    try:
        key, value = config_arg.split('=')
    except:
        error_handler(lambda: False, '%s is not a valid argument', config_arg)

    if Path(value).is_dir():
        value = Path(value).expanduser().resolve().as_posix()
    
    error_handler(lambda: key in config.DEFAULTS, '%s is not a valid config setting', key)
    error_handler(lambda: key not in CONFIG_STATES or value in CONFIG_STATES[key], '%s is not a valid value for %s', value, key)
    error_handler(lambda: key not in CONFIG_BOOLEAN or value in CONFIG_ENABLED_DICT, '%s is not a valid value for %s', value, key)
    
    return key, value

def print_full_help(parser: argparse.ArgumentParser):
    """ Custom help function that displays usage for all subcommands of CLI. """
    subparser_actions = [action for action in parser._actions if isinstance(action, argparse._SubParsersAction)]
    for sa in subparser_actions:
        for cmd, subparser in sa.choices.items():
            print(f'COMMAND: {cmd}')
            print(subparser.format_help())

def build_parser() -> argparse.ArgumentParser:
    """ Helper function that directs command line arguments to the kwex script, a set_config command, or a get_config command. """
    parser = argparse.ArgumentParser(prog='kwex')
    subparsers = parser.add_subparsers(dest='command')

    #run command activates standard kwex script
    run = subparsers.add_parser('run', description="Default command to run kwex script. 'run' can be omitted.")
    run.add_argument('template', help='<path to velocity template>')
    run.add_argument('input', nargs='+', help='<path to PDS3 files or directories>')
    run.add_argument('--output', metavar='', help='Specify a different name or path for output PDS4 labels.')
    run.add_argument('--input-root', metavar='', help='When specifying a different output directory, specify an input directory from which to preserve directory structure.')
    run.add_argument('--log', metavar='', nargs='?', const=ConfigState.BLANK, help='Include to enable logging of debug and runtime information, either to "CONSOLE" or a specified log file.')
    run.add_argument('--override', metavar='', default=None, nargs='+', help='Override one or more config values for this run with syntax <key>=<value>.')
    run.set_defaults(func=handle_run)

    #set_config command for creating/modifying custom user config file
    set_config_cmd = subparsers.add_parser('set_config', add_help=False)
    set_config_cmd.add_argument('set', help='Save config value to user config file with syntax <key>=<value>.')
    set_config_cmd.set_defaults(func=handle_set_config)

    #get_config command for displaying default config values + user config file overrides
    get_config_cmd = subparsers.add_parser('get_config', add_help=False, description='Display config values with format <key>=<value> [OPTIONS].')
    get_config_cmd.set_defaults(func=handle_get_config)

    return parser

def main(argv=None):
    """ Entry point for the kwex CLI """
    parser = build_parser()
    
    argv = sys.argv[1:]
    has_subcommand = argv and argv[0] in {'run', 'set_config', 'get_config'}
    has_help = argv and argv[0] in {'-h', '--help'}
    if has_help:
        print_full_help(parser)
        return
    elif not has_subcommand:
        #the run command is implicit if omitted, so that the standard kwex script runs by default
        argv = ['run'] + argv

    args = parser.parse_args(argv)

    cfg.load_user_file() 

    return args.func(args)

def handle_run(args: argparse.Namespace):
    """ argparse command function for creating configuration object and running main kwex script. """
    #apply config changes from cli and create config object referenced throughout program
    cfg.apply_cli_overrides(cli_override(args.override, args.log))
    config.current = cfg
    from .main import kwex_script
    kwex_script(args)

def handle_set_config(args: argparse.Namespace):
    """ argparse command function for changing configuration values. """
    key, value = config_checker(args.set)
    cfg.save_config(key, value)

def handle_get_config(args: argparse.Namespace):
    """ argparse command function for fetching configuration values. """
    config.current = cfg

    for key in cfg.values:
        if key in CONFIG_STATES:
            possible_states = '|'.join([v for v in CONFIG_STATES[key]])
            print(f'{key}={config.get_config(key)} [{possible_states}]')
        elif key in CONFIG_BOOLEAN:
            bool_value = {True: ConfigState.ENABLED, False: ConfigState.DISABLED}
            value = bool_value[config.get_config(key)]
            print(f'{key}={value} [{ConfigState.ENABLED}|{ConfigState.DISABLED}]')
        else:
            print(f'{key}={config.get_config(key)}')
