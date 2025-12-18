import subprocess
import struct
import json

from loggers.logger import get_logger
from constants import *

def compile_check(java_class: str, java_source: str) -> tuple[bool, int]:
    """ Function to check whether the Java Velocity class needs to be compiled. Does so if it doesn't exist, is incompatible with the system's Java runtime environment, or is older than its .java source file. """
    class_exists = java_class.is_file()
    system_java_version = system_version()
    
    if class_exists:
        class_java_version = class_version(java_class)
        incompatible_java = class_java_version > system_java_version
        if incompatible_java:
            get_logger().info(f'System Java version ({system_java_version}) is not compatible with version against which Java class was compiled ({class_java_version}.)')
        
        newer_source = newer(java_source, java_class)
        if newer_source:
            get_logger().info(f'{java_source} is newer than {java_class}.')
    else:
        get_logger().info(f'{java_class} does not exist.')

    return (not class_exists or incompatible_java or newer_source), system_java_version

def system_version() -> int:
    """ Utility to get the version of the system's Java runtime environment. """
    return int(subprocess.check_output(['java', '--version'], stderr=subprocess.STDOUT, encoding='utf-8').split()[1].split('.')[0])

def class_version(java_class: str) -> int:
    """ Utility to get the major version of the compiled Java class and convert to JRE version numbers. """
    major_version = str(struct.unpack(">H", java_class.read_bytes()[6:8])[0])
    #for reasons beyond my understanding, the "version" a Java class is compiled against follows a different scheme than the version of a Java runtime environment, so here's a lookup table to convert between the two.
    major_to_version = json.loads(MAJOR_TO_VERSION.read_text())
    return int(major_to_version[major_version])

def newer(file1: Path, file2: Path) -> bool:
    """ Utility to check whether file1 was modified more recently than file2. """
    return file1.stat().st_mtime > file2.stat().st_mtime

def wait_process(process: subprocess.Popen):
    """ Utility that loops until a (java) process is complete. """
    while process and process.poll() is None:
        pass