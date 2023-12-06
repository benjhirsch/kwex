import os
import regex as re
from collections import defaultdict
from subprocess import Popen
import sys
import simpleeval
import json
import spiceypy as spice
import numpy as np
from astropy.io import fits

args = sys.argv

#methods

def get_arg(param, else_name='', flag=False, req=False):
    if flag:
        #true if flag is present, false otherwise
        return param in args
    else:
        if param in args:
            try:
                #gets string that appears after parameter
                return args[args.index(param)+1].replace("'", "")
            except:
                report('%s parameter value not found' % param, out=req)
        elif not else_name == '':
            #default parameter if not present
            return else_name
        else:
            report('%s parameter not found' % param, out=req)

def report(msg, out=False):
    if debug or out:
        print(msg)

    if out:
        print('kwex exited without finishing.')
        sys.exit()

def add_to_val(vtype, kw, val, file=None, except_val='KEYWORD VALUE NOT FOUND'):
    if vtype not in val_list:
        val_list[vtype] = {}

    try:
        val_list[vtype][kw] = val
    except:
        val_list[vtype][kw] = except_val
        report('keyword %s not found in %s' % (kw, file))

def fix_path(path, kwex_dir=False, exist=False):
    if kwex_dir:
        fix_dir = os.path.dirname(os.path.realpath(__file__))
    else:
        fix_dir = os.getcwd()

    if os.path.isabs(path):
        return_path = os.path.normpath(path)
    else:
        return_path = os.path.normpath(os.path.join(fix_dir, path))

    if exist and not os.path.isfile(return_path):
        report ('%s not found.' % path, out=True)
    else:
        return return_path

def add_kv(kvd, k, v):
    if isinstance(v, str):
        if re.match(r'\((.*)?\)', v.strip()):
            #separate parenthetical lists into lists
            v = [e.strip() for e in v.strip()[1:-1].split(',')]
        elif re.search(r'<\w+>', v):
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
debug = get_arg('-d', flag=True)
fits_file = fix_path(get_arg('-f', req=True), exist=True)
vm_file = fix_path(get_arg('-v', req=True), exist=True)
pds3_file = fix_path(get_arg('-l', '%s/%s.lbl' % (os.path.dirname(fits_file), os.path.splitext(os.path.basename(fits_file))[0])), exist = get_arg('-l', flag=True))
out_file = fix_path(get_arg('-o', '%s/%s.xml' % (os.path.dirname(fits_file), os.path.splitext(os.path.basename(fits_file))[0])))
kernel_file = fix_path(get_arg('-s', 'spice/nh_v06.tm'), kwex_dir=True, exist=True)
sp_calc_file = fix_path(get_arg('-c', 'spice/spice_calcs.json'), kwex_dir=True, exist=True)
ref_frame = get_arg('-rf', 'J2000')
spacecraft = get_arg('-sc', 'NH')

#compile Velocity engine Java class
json_file = fix_path('tmp/vals.json', kwex_dir=True)
java_file = fix_path('java/VMtoXML.java', kwex_dir=True)
javac_file = fix_path('java/VMtoXML.class', kwex_dir=True)

with open(java_file) as f:
    java_str = f.read()

if not json_file == re.search(r'String jsonValFile = "(.*?)";', java_str).group(1):
    java_repl = True
    with open(java_file, 'w') as f:
        new_java_str = java_str.replace(re.search(r'String jsonValFile = "(.*?)";', java_str).group(1), json_file.replace('\\', '/'))
        q = f.write(new_java_str)
else:
    java_repl = False

if java_repl or not os.path.isfile(javac_file):
    if os.path.isfile(javac_file):
        os.remove(javac_file)
    javac_args = ['javac', '-cp', ' .;velocity-1.7.jar;velocity-tools-2.0.jar;jackson-core-2.9.9.jar;jackson-databind-2.9.9.jar', 'VMtoXML.java']
    p = Popen(javac_args, cwd=fix_path('java', kwex_dir=True), shell=True)

#get variables from template
with open(vm_file) as f:
    vm_str = ''
    for line in f:
        if '$' in line:
            vm_str += line

label_list = re.findall(r'\$label\.[\w\_\:]+(?![\w\_])', vm_str) + re.findall(r'\${label\.[\w\_\:]+}', vm_str)
label_list = sorted([v.split('.')[-1].replace('}', '') for v in set(label_list)])
report('%s PDS3 label keywords found in %s' % (len(label_list), vm_file))

fits_list = re.findall(r'\$fits\.[\w\_\:]+(?![\w\_])', vm_str) + re.findall(r'\${fits\.[\w\_\:]+}', vm_str) + re.findall(r'\$fits\_ext\d+\.[\w\_\:]+(?![\w\_])', vm_str) + re.findall(r'\${fits\_ext\d+\.[\w\_\:]+}', vm_str)
fits_list = sorted(set([v.replace('{', '').replace('}', '') for v in fits_list]))
report('%s FITS keywords found in %s' % (len(fits_list), vm_file))

spice_list = re.findall(r'\$spice\.[\w\_\:]+(?![\w\_])', vm_str) + re.findall(r'\${\spice\.[\w\_\:]+}', vm_str)
spice_list = sorted([v.split('.')[-1].replace('}', '') for v in set(spice_list)])
report('%s SPICE keywords found in %s' % (len(label_list), vm_file))

#initialize list to hold extracted values for each keyword
val_list = {'label': {}, 'fits': {}, 'spice': {}}

#get pds3 label keyword values
if label_list and os.path.isfile(pds3_file):
    kv_dict = {}
    ostack = []
    
    with open(pds3_file) as f:
        lbl_lines = [line for line in f]

    for n, line in enumerate(lbl_lines):
        #split each line into tidy keyword=value pairs
        k, v = ([p.strip() for p in line.split('=')][:2] + [None]*2)[:2]

        if v:
            #multi-line values will start with either a parenthesis or double quote
            if v.startswith(('(', '"')):
                ml_count = n+1
                while '=' not in lbl_lines[ml_count]:
                    #when you encounter a multi-line value, iterate through label until you get to the next kw=value line
                    if lbl_lines[ml_count].strip() not in ['END', '']:
                        #and add each line to the previous one
                        v = ' '.join([v, lbl_lines[ml_count].strip()])
                    ml_count += 1
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
    for kw in label_list:
        kd = '^' + kw[4:] if kw.startswith('PTR_') else kw #replace PTR_ in template with ^ because ^ in XML causes problems
        add_to_val('label', kw, kv_dict[kd], file=pds3_file)
elif label_list and not os.path.isfile(pds3_file):
    report('PDS3 keywords found in %s but PDS3 label %s not found.' % (vm_file, pds3_file), out=True)

#get FITS header keyword values
if fits_list:
    with fits.open(fits_file) as f:
        hdr_list = [h.header for h in f]
        
    for fv in fits_list:
        #identify FITS keyword extension, with none being 0
        fx, kw = fv.split('.')
        ext = re.sub(r'[^\d]', '', fx)
        ext = int(ext) if ext.isnumeric() else 0

        #find iterative FITS keywords
        val = [hdr_list[ext][ki] for ki in hdr_list[ext] if re.sub(r'\d', '', ki) == kw]
        if len(val) == 1:
            val = val[0]
        elif len(val) == 0:
            try:
                val = hdr_list[ext][kw]
                #catch non-iterative keywords with digits, like NAXIS1
            except:
                pass

        #record values of template keywords
        add_to_val(fx[1:], kw, val, file=fits_file)
        
#calculate values for SPICE keywords
if spice_list:
    if os.path.exists(kernel_file):
        target_state, target_state2, target_EARTH_state, target_SUN_state, sol_pos, helio_state, geo_state, i2j_mat, j2i_mat, fits_target_ID = init_spice(fits_file, kernel_file, ref_frame, spacecraft)
        se = init_eval()

        with open(sp_calc_file) as f:
            spice_calc = json.load(f)
            #SPICE formulas adapted from Benjamin Sharkey's spiceypy code

        #removes namespaces from numpy and spice functions because otherwise they don't work with simpleeval
        for k in spice_calc:
            spice_calc[k] = spice_calc[k].replace('np.', '').replace('spice.', '')

        for kw in spice_list:
            #se.eval translates str formulations of spice functions into something evaluable
            try:
                val = se.eval(spice_calc[kw])
            except:
                val = 'KEYWORD NOT RECALCULATED'
                report('%s keyword could not be recalculated' % kw)
            add_to_val('spice', kw, val)
    else:
        report('meta kernel file %s not found' % kernel_file, out=True)

#write temporary *.json file to feed into velocity engine
os.makedirs(fix_path('tmp', kwex_dir=True), exist_ok=True)
val_list['template_file_path'] = os.path.dirname(vm_file).replace('\\', '/')
val_list['template_file_name'] = os.path.basename(vm_file).replace('\\', '/')
val_list['output_file_name'] = out_file.replace('\\', '/')
with open(fix_path('tmp/vals.json', kwex_dir=True), 'w') as f:
    q = json.dump(val_list, f)

#run java script to activate velocity engine
java_args = ['java', '-cp', '.;velocity-1.7.jar;velocity-tools-2.0.jar;jackson-core-2.9.9.jar;jackson-databind-2.9.9.jar;jackson-annotations-2.9.9.jar;commons-collections-3.2.2.jar;commons-lang-2.4.jar', 'VMtoXML']
while not os.path.isfile('java/VMtoXML.class'):
    pass
p = Popen(java_args, cwd=fix_path('java', kwex_dir=True), shell=True)
