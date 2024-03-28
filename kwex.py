import os
import regex as re
import sys
import simpleeval
import json
import spiceypy as spice
import numpy as np
from astropy.io import fits
import argparse
from glob import glob

from spice import kspice
from pds3 import pds3_parser
from java import kjava

#methods

def report(msg, out=False):
    if args.debug or out:
        print(msg)

    if out:
        print('kwex exited without finishing.')
        sys.exit()

def add_to_val(vtype, kw, val=None, fnc_var=None, val_fnc=None, file=None, except_val='KEYWORD VALUE NOT FOUND'):
    if vtype not in val_list:
        #this will catch FITS extensions and anything else strange
        val_list[vtype] = {}

    if val_fnc:
        #if there's a function in the arguments, generate val by running that function
        if not fnc_var:
            #if no explicit function variable is given, use kw
            fnc_var = kw
        try:
            val = val_fnc(fnc_var)
        except Exception as e:
            val = except_val
            report('keyword %s value not found because %s' % (kw, e))

    val_list[vtype][kw] = val

def fix_path(path, kwex_dir=False, exist=False):
    if kwex_dir:
        fix_dir = os.path.dirname(os.path.realpath(__file__))
    else:
        fix_dir = os.getcwd()

    if os.path.isabs(path):
        return_path = os.path.normpath(path)
    else:
        return_path = os.path.normpath(os.path.join(fix_dir, path))

    if exist and not ('*' in return_path or os.path.isfile(return_path)):
        #exit program if a file is required and not present and there's no wildcard
        report ('%s not found.' % return_path, out=True)
    else:
        return return_path

def init_eval(ksp):
    se = simpleeval.SimpleEval()
    se.names['ksp'] = ksp
    se.names['i2j_mat'] = ksp.i2j_mat
    se.names['j2i_mat'] = ksp.j2i_mat
    se.names['sol_pos'] = ksp.sol_pos
    se.names['target_pole_j2000_rec'] = ksp.target_pole_j2000_rec
    se.names['target_name'] = ksp.spice_target_name
    se.names['minus_x_axis'] = [-1, 0, 0]
    se.names['j2000_north'] = [0, 0, 1]
    se.functions['multiply'] = np.multiply
    se.functions['recrad'] = spice.recrad
    se.functions['mxv'] = spice.mxv
    se.functions['dpr'] = spice.dpr
    se.functions['arctan2'] = np.arctan2
    se.functions['m2q'] = spice.m2q
    se.functions['vnorm'] = spice.vnorm

    return se

#get command line arguments
parser = argparse.ArgumentParser(description='KeyWord EXtraction tool for PDS3-to-PDS4 migration')

parser.add_argument('-v', metavar='template', dest='template',required=True, help='<path to velocity template>')
parser.add_argument('-f', dest='fits', required=True, help='<path to fits file>')
parser.add_argument('-l', dest='label', metavar='PDS3 label', help='Specifies a different name for the PDS3 label file.')
parser.add_argument('-o', metavar='output', dest='output', help='Specifies a different name for the output file.')
parser.add_argument('-e', dest='ext', metavar='extension', default='xml', help='Specifies the output file extension (when not provided by -o). Default is .xml.')
parser.add_argument('-d', dest='debug', action='store_true', help='Prints some minimal debugging to the console.')
parser.add_argument('--kernel', metavar='', default='spice/nh_v06.tm', help='Specifies a different SPICE kernel. Default is ./spice/nh_v06.tm')
parser.add_argument('--calcs', metavar='', dest='spice_calcs', default='spice/spice_calcs.json', help='Specifies a different spice calculations file.')
parser.add_argument('--ref', metavar='', dest='ref_frame', default='J2000', help='Specifies a different reference frame for SPICE. Default is J2000.')
parser.add_argument('--sc', metavar='', dest='spacecraft', default='NH', help='Specifies a different spacecraft for SPICE. Default is NH (NEW HORIZONS).')
parser.add_argument('--vals', dest='keep_json', action='store_true', help='Include to not delete vals.json at end of program.')

args = parser.parse_args()

vm_file = fix_path(args.template, exist=True)

fits_file = fix_path(args.fits, exist=True)
fits_glob = glob(fits_file) #convert wildcard argument to list
if len(fits_glob) == 0:
    #if wildcard returns no files, quit
    report('no files found in path %s' % fits_file, out=True)
else:
    fits_file = fits_glob

pds3_file = []
out_file = []

#if glob gets multiple fits files, name the corresponding pds3 and pds4 labels accordingly
for file in fits_file:
    fits_dir = os.path.dirname(file)
    fits_fn = os.path.splitext(os.path.basename(file))[0]

    if args.label:
        pds3_file.append(fix_path(args.label, exist=True))
    else:
        pds3_file.append(fix_path('%s/%s.lbl' % (fits_dir, fits_fn), exist=True))

    if args.output:
        out_file.append(fix_path(args.output))
    else:
        out_file.append(fix_path('%s/%s.%s' % (fits_dir, fits_fn, args.ext)))

#compile Velocity engine Java class
json_file = fix_path('tmp/vals.json', kwex_dir=True)
java_file = fix_path('java/%s.java' % kjava.CLASSNAME, kwex_dir=True, exist=True)
javac_file = fix_path('java/%s.class' % kjava.CLASSNAME, kwex_dir=True)

java_repl = False #for testing purposes only
java_compile, compile_msg, system_java_version = kjava.compile_check(java_file, javac_file)
for msg in compile_msg:
    report(msg)

if java_compile or java_repl:
    report('Compiling Velocity engine Java class...')
    javac_process = kjava.java_process('javac', '%s.java' % kjava.CLASSNAME, fix_path('java', kwex_dir=True), version=system_java_version)
else:
    javac_process = None

#get variables from template
with open(vm_file) as f:
    vm_str = ''
    vm_nows = ''
    current_line = ''
    in_velocity = False
    open_char = ['(', '{', '[']
    close_char = [')', '}', ']']

    for line in f:
        if '$' in line:
            #we only need to get template lines that include variable pointers
            vm_str += line

        #and write modified template with whitespace removed
        lstrip = line.strip()
        if not in_velocity:
            if lstrip.startswith('#'):
                #if at the start of a velocity code block, register that and don't add line
                in_velocity = True
            else:
                #if not in a velocity code block, add line as normal
                vm_nows += line

        if in_velocity:
            #if in a velocity code block, add this line to the overall current line
            current_line += lstrip
            if (any([c in line for c in close_char]) and sum([current_line.count(op) for op in open_char]) == sum([current_line.count(cl) for cl in close_char])) or (any([lstrip == c for c in ['#end', '#else']])):
                #if all parentheses are closed or there's an #end or #else statement, get out of velocity code block
                in_velocity = False
                vm_nows += '%s##\n' % current_line
                current_line = ''

with open(os.path.join(os.path.dirname(vm_file), 'nows_%s' % (os.path.basename(vm_file))), 'w') as f:
    q = f.write(vm_nows)
    #record template with whitespace removed

label_list = re.findall(r'\$label\.[\w\_\:]+(?![\w\_])', vm_str) + re.findall(r'\${label\.[\w\_\:]+}', vm_str) #$label. followed by 1+ alphanumeric characters, underscores, or colons + the same but with label.<alphanumeric characters> enclosed in curly brackets
label_list = sorted([v.split('.')[-1].replace('}', '') for v in set(label_list)])
report('%s PDS3 label keywords found in %s' % (len(label_list), os.path.basename(vm_file)))

fits_list = re.findall(r'\$fits\.[\w\_\:]+(?![\w\_])', vm_str) + re.findall(r'\${fits\.[\w\_\:]+}', vm_str) + re.findall(r'\$fits\_ext\d+\.[\w\_\:]+(?![\w\_])', vm_str) + re.findall(r'\${fits\_ext\d+\.[\w\_\:]+}', vm_str) #as above (but with fits), plus fits_ext<1+ digits>
fits_list = sorted(set([v.replace('{', '').replace('}', '') for v in fits_list]))
report('%s FITS keywords found in %s' % (len(fits_list), os.path.basename(vm_file)))

spice_list = re.findall(r'\$spice\.[\w\_\:]+(?![\w\_])', vm_str) + re.findall(r'\${\spice\.[\w\_\:]+}', vm_str)
spice_list = sorted([v.split('.')[-1].replace('}', '') for v in set(spice_list)])
report('%s SPICE keywords found in %s\n' % (len(spice_list), os.path.basename(vm_file)))

for file_count, file in enumerate(fits_file):
    #print(file)
    #initialize list to hold extracted values for each keyword
    val_list = {'label': {}, 'fits': {}, 'spice': {}}

    #get pds3 label keyword values
    if label_list and os.path.isfile(pds3_file[file_count]):
        report('Reading PDS3 label %s...' % os.path.basename(pds3_file[file_count]))
        kv_dict = pds3_parser.parse(pds3_file[file_count])
                                
        #record values of keywords found in template
        with open(fix_path('pds3/var_sub.json', kwex_dir=True)) as sf:
            #load PDS3 keyword variable substitution file
            var_sub = json.load(sf)

        sub_check = {'start': lambda x: '^%s' % x, 'in': lambda x: x, 'end': lambda x: '%s$' % x}
        for kw in label_list:
            kd = kw
            for sub in var_sub:
                #for each possible variable substitution, check if the Java sub is in the right place, then replace with PDS3 original
                kd = re.sub(sub_check[var_sub[sub]['pos']](sub), var_sub[sub]['sub'], kd)
            add_to_val('label', kw, fnc_var=kd, val_fnc=lambda x: kv_dict[x], file=pds3_file[file_count])
        
    elif label_list and not os.path.isfile(pds3_file[file_count]):
        report('PDS3 keywords found in %s but PDS3 label %s not found.' % (vm_file, pds3_file[file_count]), out=True)

    #get FITS header keyword values
    if fits_list:
        report('Reading FITS file %s...' % os.path.basename(file))
        with fits.open(file) as f:
            hdr_list = [h.header for h in f]
            
        for fv in fits_list:
            #identify FITS keyword extension, with none being 0
            fx, kw = fv.split('.')
            ext = re.sub(r'[^\d]', '', fx) #sub out digits
            ext = int(ext) if ext.isnumeric() else 0

            #find iterative FITS keywords
            try:
                iter_list = [hdr_list[ext][ki] for ki in hdr_list[ext] if re.sub(r'\d', '', ki) == kw]
            except:
                iter_list = []

            #record values of template keywords
            if len(iter_list) > 1:
                add_to_val(fx[1:], kw, val=iter_list, file=file)
            else:
                add_to_val(fx[1:], kw, val_fnc=lambda x: hdr_list[ext][x], file=file)

    #calculate values for SPICE keywords
    if spice_list:
        report('Calculating spice keywords...')
        if file_count == 0: #only need to initialize spice stuff once
            kernel_file = fix_path(args.kernel, kwex_dir=True, exist=True)
            #check if kernel PATH_VALUE is relative or wrong and switch to absolute and correct
            with open(kernel_file) as f:
                kernel_str = f.read()
            kernel_path_value = re.search(r"PATH_VALUES\s+=\s+\(\n\s+'(.+)'", kernel_str).group(1)
            kernel_path_repl = os.path.normpath(os.path.join(os.path.dirname(kernel_file), 'data')).replace('\\', '/')
            if not (os.path.isabs(kernel_path_value) or os.path.normpath(kernel_path_value).replace('\\', '/') == kernel_path_repl):
                kernel_str_repl = re.sub(r"(?<=PATH_VALUES\s+=\s+\(\n\s+').+(?=')", kernel_path_repl, kernel_str)
                report('Switching PATH_VALUE in %s from %s to %s' % (os.path.basename(kernel_file), kernel_path_value, kernel_path_repl))
                with open(kernel_file, 'w') as f:
                    q = f.write(kernel_str_repl)

            sp_calc_file = fix_path(args.spice_calcs, kwex_dir=True, exist=True)
            ref_frame = args.ref_frame
            spacecraft = args.spacecraft

            with open(sp_calc_file) as f:
                spice_calc = json.load(f)
                #SPICE formulas adapted from Benjamin Sharkey's spiceypy code

            #removes namespaces from numpy and spice functions because otherwise they don't work with simpleeval
            for k in spice_calc:
                spice_calc[k] = spice_calc[k].replace('np.', '').replace('spice.', '')

        ksp = kspice.KwexSpice(file, kernel_file, ref_frame, spacecraft)
        se = init_eval(ksp)

        for kw in spice_list:
            #se.eval translates str formulations of spice functions into something evaluable
            add_to_val('spice', kw, val_fnc=lambda x: se.eval(spice_calc[x]), file=sp_calc_file, except_val='KEYWORD NOT RECALCULATED')

    #write temporary *.json file to feed into velocity engine
    os.makedirs(fix_path('tmp', kwex_dir=True), exist_ok=True)
    json_file_n = json_file.replace('vals.json', 'vals_%s.json' % file_count)
    report('Recording keyword values in %s...' % os.path.basename(json_file_n))
    with open(json_file_n, 'w') as f:
        q = json.dump(val_list, f, indent=4)

    #run java script to activate velocity engine
        
    #set arguments to pass to java main
    template_file_path = os.path.dirname(vm_file).replace('\\', '/')
    template_file_name = 'nows_' + os.path.basename(vm_file).replace('\\', '/')
    output_file_name = out_file[file_count].replace('\\', '/')

    #wait until java class is compiled before proceeding
    while javac_process and javac_process.poll() is None:
        pass
    report('Activating velocity engine and writing PDS4 label %s...\n' % os.path.basename(out_file[file_count]))
    velocity_process = kjava.java_process('java', kjava.CLASSNAME, fix_path('java', kwex_dir=True), json_file_n, template_file_path, template_file_name, output_file_name)

if not args.keep_json:
    json_list = glob('%s/*.json' % os.path.dirname(json_file))
    #once velocity is done running, delete temporary json value files
    while velocity_process.poll() is None:
        pass

    for j in json_list:
        os.remove(j)

#remove temporary template with whitespace removed
os.remove(os.path.join(os.path.dirname(vm_file), 'nows_%s' % (os.path.basename(vm_file))))
