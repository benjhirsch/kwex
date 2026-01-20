import subprocess

from ..constants import *
from ..state import run_state
from ..config import get_config
from ..names import ConfigKey
from ..loggers import *
from ..utils import *

def init_velocity(template_path: Path) -> subprocess.Popen:
    if get_config(ConfigKey.VELOCITY):
        template_file_path = template_path.parent.as_posix()
        template_file_name = template_path.name

        wait_process(run_state.java_compile_process)
        info_logger('Activating Velocity engine')

        velocity_process = java_process('java', JAVA_CLASS.stem, USER_DIR, template_file_path, template_file_name, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        run_state.velocity_process = velocity_process

def terminate_velocity():
    terminate_command = {'cmd': 'terminate'}
    try:
        run_state.velocity_process.stdin.write(fix_json(terminate_command))
        run_state.velocity_process.stdin.flush()
    except:
        pass
    finally:
        run_state.velocity_process.stdin.close()
        run_state.velocity_process.wait()

def compile_velocity():
    """ Wrapper function to compile the Java class that runs the Velocity engine from a .java source file. """
    yes, system_java_version = compile_check(JAVA_CLASS, JAVA_SOURCE)

    if yes:
        #if the java velocity class doesn't exist, was compiled with an incompatible version of java, or is older than its .java source file, recompile
        info_logger('Compiling Java class from source %s', JAVA_SOURCE.name)
        USER_DIR.mkdir(parents=True, exist_ok=True)
        proc = java_process('javac', JAVA_SOURCE, JAVA_DIR, '-d', USER_DIR, version=str(system_java_version))
        run_state.java_compile_process = proc
