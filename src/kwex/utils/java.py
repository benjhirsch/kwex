import subprocess
import struct
import json
import os

from ..loggers import *
from ..constants import *

def compile_check(java_class: Path, java_source: Path) -> tuple[bool, int]:
    """ Function to check whether the Java Velocity class needs to be compiled. Does so if it doesn't exist, is incompatible with the system's Java runtime environment, or is older than its .java source file. """
    class_exists = java_class.is_file()
    system_java_version = _system_version()
    
    if class_exists:
        class_java_version = _class_version(java_class)
        incompatible_java = class_java_version > system_java_version
        if incompatible_java:
            info_logger('System Java version (%s) is not compatible with version against which Java class was compiled (%s)', system_java_version, class_java_version)
        
        newer_source = _newer(java_source, java_class)
        if newer_source:
            info_logger('%s is newer than %s', java_source.name, java_class.name)
    else:
        info_logger('%s does not exist', java_class.name)

    return (not class_exists or incompatible_java or newer_source), system_java_version

def _system_version() -> int:
    """ Utility to get the version of the system's Java runtime environment. """
    return int(subprocess.check_output(['java', '--version'], stderr=subprocess.STDOUT, encoding='utf-8').split()[1].split('.')[0])

def _class_version(java_class: str) -> int:
    """ Utility to get the major version of the compiled Java class and convert to JRE version numbers. """
    major_version = str(struct.unpack(">H", java_class.read_bytes()[6:8])[0])
    #for reasons beyond my understanding, the "version" a Java class is compiled against follows a different scheme than the version of a Java runtime environment, so here's a lookup table to convert between the two.
    major_to_version = json.loads(MAJOR_TO_VERSION.read_text())
    return int(major_to_version[major_version])

def _newer(file1: Path, file2: Path) -> bool:
    """ Utility to check whether file1 was modified more recently than file2. """
    return file1.stat().st_mtime > file2.stat().st_mtime

def wait_process(process: subprocess.Popen):
    """ Utility that loops until a (java) process is complete. """
    while process and process.poll() is None:
        pass

def java_process(command: str, file: str, cwd: str, *args, version=None, **kwargs) -> subprocess.Popen:
    """ Wrapper function to run Java comands. """
    jargs = [command]
    if version is not None:
        jargs += ['--target', version]

    jar_files = os.pathsep.join([(JAVA_DIR / j).as_posix() for j in [cwd]+JAR_FILES])
    jargs += ['-cp', jar_files, file, *args]

    proc = subprocess.Popen(jargs, cwd=cwd, **kwargs)
    return proc
