import os
import regex as re
import subprocess

CLASSNAME = 'VMtoXML'

def compile_check(java_file, class_file):
    system_java_version = system_version()
    class_exists = os.path.isfile(class_file)
    msg = []

    if class_exists:
        file_java_version = file_version(class_file)

        version_mismatch = not (int(system_java_version) == file_java_version)
        if version_mismatch:
            msg.append('System Java version (%s) does not match version against which Java class was compiled (%s)' % (system_java_version, file_java_version))

        newer_java = newer(java_file, class_file)
        if newer_java:
            msg.append('%s is newer than %s' % (os.path.basename(java_file), os.path.basename(class_file)))
    else:
        msg.append('%s does not exist' % os.path.basename(class_file))

    return (not class_exists or version_mismatch or newer_java), msg, system_java_version

def system_version():
    return re.search(r'java\sversion\s\"(\d+)\.', str(subprocess.check_output(['java', '-version'], stderr=subprocess.STDOUT))).group(1)

def file_version(file):
    with open(file, 'rb') as f:
        file_binary = f.read()

    return sum(file_binary[6:8])-44

def newer(file1, file2):
    return os.path.getmtime(file1) > os.path.getmtime(file2)

def java_process(command, file, cwd, *args, version=None):
    jargs = [command]
    if version is not None:
        jargs += ['--target', version]

    jar_files = os.pathsep.join(['.', 'velocity-1.7.jar', 'velocity-tools-2.0.jar', 'jackson-core-2.9.9.jar', 'jackson-databind-2.9.9.jar', 'jackson-annotations-2.9.9.jar', 'commons-collections-3.2.2.jar', 'commons-lang-2.4.jar'])
    jargs += ['-cp', jar_files, file, *args]

    proc = subprocess.Popen(jargs, cwd=cwd)
    return proc
