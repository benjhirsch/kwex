import subprocess

from ..constants import *
from ..state import run_state
from ..config import get_config
from ..names import ConfigKey
from ..loggers import *
from ..utils import *

def run_velocity(val_list: dict, output_path: Path) -> subprocess.Popen:
    """ Wrapper function to activate the Velocity template engine via Java. """
    #just in case, wait until java class is compiled before proceeding

    json_vals = send_values(val_list, output_path)
    run_state.json_list.append(json_vals)

    if get_config(ConfigKey.VELOCITY):
        #collect filenames to send as arguments to velocity engine
        json_file_name = json_vals.as_posix()
        template_file_path = run_state.nows_template_filename.parent.as_posix()
        template_file_name = run_state.nows_template_filename.name
        output_file_name = output_path.as_posix()

        wait_process(run_state.java_compile_process)
        info_logger(f'Activating Velocity engine and writing PDS4 label {output_path.name}')

        velocity_process = java_process('java', JAVA_CLASS.stem, USER_DIR, json_file_name, template_file_path, template_file_name, output_file_name)
        run_state.velocity_process = velocity_process

def compile_velocity():
    """ Wrapper function to compile the Java class that runs the Velocity engine from a .java source file. """
    yes, system_java_version = compile_check(JAVA_CLASS, JAVA_SOURCE)

    if yes:
        #if the java velocity class doesn't exist, was compiled with an incompatible version of java, or is older than its .java source file, recompile
        info_logger(f'Compiling Java class from source {JAVA_SOURCE.name}')
        USER_DIR.mkdir(parents=True, exist_ok=True)
        proc = java_process('javac', JAVA_SOURCE, JAVA_DIR, '-d', USER_DIR, version=str(system_java_version))
        run_state.java_compile_process = proc
