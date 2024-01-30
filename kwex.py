import os
import regex as re
from subprocess import Popen
import sys
import simpleeval
import json
import spiceypy as spice
import numpy as np
from astropy.io import fits
import argparse
from glob import glob

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
        except:
            val = except_val
            report('keyword %s not found in %s' % (kw, file))

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

def add_kv(kvd, k, v):
    if isinstance(v, str):
        if re.match(r'(\((.*)?\))|(\{(.*)?\})', v.strip()):
            #separate parenthetical lists into lists
            listv = [e.strip() for e in v.strip()[1:-1].split(',')]
            #send each element through add_kv individually
            v = [add_kv({}, n, elem)[n] for n, elem in enumerate(listv)]
        elif not v.startswith('"') and re.search(r'<\w+>', v):
            #turn values of the form "VALUE <UNIT>" into dictionaries with value and unit keys
            try:
                v = {'value': re.search(r'^(.*?)\s*<.*?>', v).group(1), 'unit': re.search(r'<\w+>', v).group(0)[1:-1]}
            except:
                pass
    if k in kvd:
        #if a keyword is already in the dictionary, either turn the value into a list or add to the value list already there
        if not isinstance(kvd[k], list):
            kvd[k] = [kvd[k]]
        kvd[k].append(v)
    else:
        kvd[k] = v

    return kvd

def init_eval():
    se = simpleeval.SimpleEval()
    se.names['target_state'] = target_state
    se.names['sol_pos'] = sol_pos
    se.names['helio_state'] = helio_state
    se.names['geo_state'] = geo_state
    se.names['i2j_mat'] = i2j_mat
    se.names['j2i_mat'] = j2i_mat
    se.names['fits_target_ID'] = fits_target_ID
    se.names['minus_x_axis'] = [-1, 0, 0]
    se.names['j2000_north'] = [0, 0, 1]
    se.names['target_EARTH_state'] = target_EARTH_state
    se.names['target_SUN_state'] = target_SUN_state
    se.names['target_state2'] = target_state2
    se.functions['multiply'] = np.multiply
    se.functions['recrad'] = spice.recrad
    se.functions['mxv'] = spice.mxv
    se.functions['dpr'] = spice.dpr
    se.functions['arctan2'] = np.arctan2
    se.functions['m2q'] = spice.m2q
    se.functions['vnorm'] = spice.vnorm
    se.functions['bodn2c'] = spice.bodn2c

    return se

def init_spice(fits_file, kernel_file, ref_frame, spacecraft, abcorr='LT+S'):
    #adapted from Benjamin Sharkey's spiceypy code
    spice.kclear()
    cwd = os.getcwd()
    os.chdir(os.path.dirname(kernel_file))
    spice.furnsh(kernel_file)
    os.chdir(cwd)
    
    with fits.open(fits_file) as f:
        hdr = f[0].header
    sclk = hdr['SPCSCLK']
    instr_frame=hdr['SPCINSTR']
    et = spice.scs2e(-98, sclk)
    
    try:
        target_state, target_lightTimes = spice.spkezr(hdr['SPCTCB'], et, ref_frame, abcorr, spacecraft)
        target_state2, target_lightTimes2 = spice.spkezr(spacecraft, et, ref_frame, abcorr, hdr['SPCTCB'])
        target_EARTH_state, target_EARTH_lightTimes = spice.spkezr(hdr['SPCTCB'], et, ref_frame, abcorr, 'EARTH')
        target_SUN_state, target_SUN_lightTimes = spice.spkezr(hdr['SPCTCB'], et, ref_frame, abcorr, 'SUN')
    except:
        target_state = None
        target_state2 = None
        target_SUN_state = None
        target_EARTH_state = None

    try:
        i2j_mat = spice.pxform(instr_frame, ref_frame, et)
        j2i_mat = spice.pxform(ref_frame, instr_frame, et)
        sol_pos, sol_ltt = spice.spkpos('Sun', et, instr_frame, abcorr, spacecraft)
    except:
        i2j_mat = None
        j2i_mat = None
        sol_pos = None
    
    fits_target_ID = hdr['SPCTCB']
    helio_state, helio_lightTimes = spice.spkezr(spacecraft, et, ref_frame, abcorr, 'SUN')
    geo_state, geo_lightTimes = spice.spkezr(spacecraft, et, ref_frame, abcorr, 'EARTH')
    return target_state, target_state2, target_EARTH_state, target_SUN_state, sol_pos, helio_state, geo_state, i2j_mat, j2i_mat, fits_target_ID

#get command line arguments
parser = argparse.ArgumentParser(description='KeyWord EXtraction tool for PDS3-to-PDS4 migration')

parser.add_argument('-v', dest='template',required=True, help='<path to velocity template>')
parser.add_argument('-f', dest='fits', required=True, help='<path to fits file>')
parser.add_argument('-l', dest='label', metavar='PDS3 label', help='Specifies a different name for the PDS3 label file.')
parser.add_argument('-o', dest='output', help='Specifies a different name for the output file.')
parser.add_argument('-d', dest='debug', action='store_true', help='Prints some minimal debugging to the console.')
parser.add_argument('-k', dest='kernel', metavar='spice kernel', default='spice/nh_v06.tm', help='Include to calculate SPICE keywords.')
parser.add_argument('-c', dest='spice_calcs', metavar='spice calcs', default='spice/spice_calcs.json', help='Specifies a different spice calculations file.')
parser.add_argument('-r', dest='ref_frame', metavar='reference frame', default='J2000', help='Specifies a different reference frame for SPICE. Default is J2000.')
parser.add_argument('-s', dest='spacecraft', default='NH', help='Specifies a different spacecraft for SPICE. Default is NH (NEW HORIZONS).')
parser.add_argument('-j', dest='keep_json', action='store_true', help='Include to not delete vals.json at end of program.')
parser.add_argument('-x', dest='ext', metavar='output extension', default='xml', help='Specifies the output file extension (when not provided by -o). Default is .xml.')

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

for file in fits_file:
    fits_dir = os.path.dirname(file)
    fits_fn = os.path.splitext(os.path.basename(file))[0]

    if args.label:
        pds3_file.append(fix_path(args.label, exist=True))
    else:
        pds3_file.append(fix_path('%s/%s.lbl' % (fits_dir, fits_fn), exist=True))
        #report('PDS3 label file: %s' % os.path.basename(pds3_file))

    if args.output:
        out_file.append(fix_path(args.output))
    else:
        out_file.append(fix_path('%s/%s.%s' % (fits_dir, fits_fn, args.ext)))
        #report('Output file: %s' % os.path.basename(out_file))

#compile Velocity engine Java class
json_file = fix_path('tmp/vals.json', kwex_dir=True)
java_file = fix_path('java/VMtoXML.java', kwex_dir=True)
javac_file = fix_path('java/VMtoXML.class', kwex_dir=True)

with open(java_file) as f:
    java_str = f.read()

if not json_file.replace('\\', '/') == re.search(r'String jsonValFile = "(.*?)";', java_str).group(1):
    #if the specified json file is not in the .java file, rewrite the java with the new file name
    java_repl = True
    with open(java_file, 'w') as f:
        new_java_str = java_str.replace(re.search(r'String jsonValFile = "(.*?)";', java_str).group(1), json_file.replace('\\', '/'))
        q = f.write(new_java_str)
    report('Rewriting Java class with reference to %s' % json_file)
else:
    java_repl = False

if java_repl or not os.path.isfile(javac_file):
    #if the java was rewritten or there is no .class file, compile a new .class file
    if os.path.isfile(javac_file):
        os.remove(javac_file)
        report('Recompiling Java class')
    else:
        report('Compiling Java class')
    jar_files = os.pathsep.join(['.', 'velocity-1.7.jar', 'velocity-tools-2.0.jar', 'jackson-core-2.9.9.jar', 'jackson-databind-2.9.9.jar'])
    javac_args = ['javac', '-cp', jar_files, 'VMtoXML.java']
    p = Popen(javac_args, cwd=fix_path('java', kwex_dir=True))

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

label_list = re.findall(r'\$label\.[\w\_\:]+(?![\w\_])', vm_str) + re.findall(r'\${label\.[\w\_\:]+}', vm_str)
label_list = sorted([v.split('.')[-1].replace('}', '') for v in set(label_list)])
report('%s PDS3 label keywords found in %s' % (len(label_list), vm_file))

fits_list = re.findall(r'\$fits\.[\w\_\:]+(?![\w\_])', vm_str) + re.findall(r'\${fits\.[\w\_\:]+}', vm_str) + re.findall(r'\$fits\_ext\d+\.[\w\_\:]+(?![\w\_])', vm_str) + re.findall(r'\${fits\_ext\d+\.[\w\_\:]+}', vm_str)
fits_list = sorted(set([v.replace('{', '').replace('}', '') for v in fits_list]))
report('%s FITS keywords found in %s' % (len(fits_list), vm_file))

spice_list = re.findall(r'\$spice\.[\w\_\:]+(?![\w\_])', vm_str) + re.findall(r'\${\spice\.[\w\_\:]+}', vm_str)
spice_list = sorted([v.split('.')[-1].replace('}', '') for v in set(spice_list)])
report('%s SPICE keywords found in %s' % (len(spice_list), vm_file))

for file_count, file in enumerate(fits_file):
    #initialize list to hold extracted values for each keyword
    val_list = {'label': {}, 'fits': {}, 'spice': {}}

    #get pds3 label keyword values
    if label_list and os.path.isfile(pds3_file[file_count]):
        kv_dict = {}
        ostack = []
        mchar = {'(': ')', '{': '}', '"': '"'}
        
        with open(pds3_file[file_count]) as f:
            lbl_lines = [line for line in f]

        for n, line in enumerate(lbl_lines):
            #split each line into tidy keyword=value pairs
            k, v = ([p.strip() for p in line.split('=')][:2] + [None]*2)[:2]

            if v:
                #multi-line values will start with (, {, or "
                if v.startswith(tuple(mchar.keys())):
                    mstop = mchar[v[0]] #multi-line ends with closing version of what it opened with
                    ml_count = n
                    current_line = v
                    while mstop not in current_line or (ml_count == n and v == '"'):
                        #iterate through lines until you get to the stop character, but make sure you keep going if the first line is just a "
                        ml_count += 1
                        current_line = lbl_lines[ml_count].strip()
                        v += ' %s' % current_line
                        #and add each successive line to the multi-line value
                elif k == 'OBJECT':
                    #at the start of a new object, add to the object stack and return to the top of the loop
                    ostack.append([v, {}])
                    continue
                elif k == 'END_OBJECT':
                    k, v = ostack.pop()
                    #at the end of an object, remove the most recent object from the stack and assign it to the kw=val pair

                if ostack:
                    ostack[-1][-1] = add_kv(ostack[-1][-1], k, v)
                    #if we're in an object, this line's kw=val pair is added to the object instead of the label dictionary
                else:
                    kv_dict = add_kv(kv_dict, k, v)
                                
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
        with fits.open(file) as f:
            hdr_list = [h.header for h in f]
            
        for fv in fits_list:
            #identify FITS keyword extension, with none being 0
            fx, kw = fv.split('.')
            ext = re.sub(r'[^\d]', '', fx)
            ext = int(ext) if ext.isnumeric() else 0

            #find iterative FITS keywords
            iter_list = [hdr_list[ext][ki] for ki in hdr_list[ext] if re.sub(r'\d', '', ki) == kw]

            #record values of template keywords
            if len(iter_list) > 1:
                add_to_val(fx[1:], kw, val=iter_list, file=file)
            else:
                add_to_val(fx[1:], kw, val_fnc=lambda x: hdr_list[ext][x], file=file)
            
    #calculate values for SPICE keywords
    if spice_list:
        kernel_file = fix_path(args.kernel, kwex_dir=True, exist=True)
        sp_calc_file = fix_path(args.spice_calcs, kwex_dir=True, exist=True)
        ref_frame = args.ref_frame
        spacecraft = args.spacecraft

        if os.path.exists(kernel_file):
            target_state, target_state2, target_EARTH_state, target_SUN_state, sol_pos, helio_state, geo_state, i2j_mat, j2i_mat, fits_target_ID = init_spice(file, kernel_file, ref_frame, spacecraft)
            se = init_eval()

            with open(sp_calc_file) as f:
                spice_calc = json.load(f)
                #SPICE formulas adapted from Benjamin Sharkey's spiceypy code

            #removes namespaces from numpy and spice functions because otherwise they don't work with simpleeval
            for k in spice_calc:
                spice_calc[k] = spice_calc[k].replace('np.', '').replace('spice.', '')

            for kw in spice_list:
                #se.eval translates str formulations of spice functions into something evaluable
                add_to_val('spice', kw, val_fnc=lambda x: se.eval(spice_calc[x]), file=sp_calc_file, except_val='KEYWORD NOT RECALCULATED')
        else:
            report('meta kernel file %s not found' % kernel_file, out=True)

    #write temporary *.json file to feed into velocity engine
    os.makedirs(fix_path('tmp', kwex_dir=True), exist_ok=True)
    val_list['template_file_path'] = os.path.dirname(vm_file).replace('\\', '/')
    val_list['template_file_name'] = 'nows_' + os.path.basename(vm_file).replace('\\', '/')
    val_list['output_file_name'] = out_file[file_count].replace('\\', '/')
    with open(fix_path('tmp/vals.json', kwex_dir=True), 'w') as f:
        q = json.dump(val_list, f, indent=4)

    #run java script to activate velocity engine
    jar_files = os.pathsep.join(['.', 'velocity-1.7.jar', 'velocity-tools-2.0.jar', 'jackson-core-2.9.9.jar', 'jackson-databind-2.9.9.jar', 'jackson-annotations-2.9.9.jar', 'commons-collections-3.2.2.jar', 'commons-lang-2.4.jar'])
    java_args = ['java', '-cp', jar_files, 'VMtoXML']
    while not os.path.isfile('java/VMtoXML.java'):
        pass
    p = Popen(java_args, cwd=fix_path('java', kwex_dir=True))

    #delete temporary files once velocity has finished
    while p.poll() is None:
        pass
    if not args.keep_json:
        os.remove(fix_path('tmp/vals.json', kwex_dir=True))

os.remove(os.path.join(os.path.dirname(vm_file), 'nows_%s' % (os.path.basename(vm_file))))
