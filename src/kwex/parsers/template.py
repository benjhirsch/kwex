from pathlib import Path
import regex as re

from ..loggers.logger import get_logger
from ..loggers.interrupter import error_handler
from ..state import run_state
from ..names import Source

def get_vars() -> tuple[dict, str]:
    """ Parser that reads a .vm Velocity template file and retrieves variable pointers to PDS3, FITS, and SPICE keywords. """
    template = run_state.args.template
    vm_str = ''
    vm_nows = ''
    current_line = ''
    in_velocity = False

    template_path = Path(template).expanduser().resolve()
    error_handler(lambda: template_path.is_file(), f'Template file {template_path.name} not found.')

    with open(template) as f:
        for line in f:
            if '$' in line:
                #we only need to get template lines that include variable pointers
                vm_str += line

            vm_nows, current_line, in_velocity = build_nows_template(line, vm_nows, current_line, in_velocity)

    label_list = find_vars(r'\$(?:label\.|\{label\.)(\w+)(?:\})?', vm_str)
    #$label.<1+ alphanumeric characters or underscoress> and ${label.<1+ alphanumeric characters or underscoress>}
    get_logger().info(f'{len(label_list)} PDS3 label keywords found in template.')
    run_state.var_list[Source.PDS3] = label_list

    fits_list = find_vars(r'\$(?:\{)?fits(?:\.ext(\d+))?\.(\w+)(?:\})?', vm_str, groups=[1, 2])
    #as above (but with fits), plus fits_<1+ digits> for FITS extensions
    get_logger().info(f'{len(fits_list)} FITS keywords found in template.')
    run_state.var_list[Source.FITS] = fits_list

    spice_list = find_vars(r'\$(?:spice\.|\{spice\.)(\w+)(?:\})?', vm_str)
    #as $label, but spice.
    get_logger().info(f'{len(spice_list)} SPICE keywords found in template.')
    run_state.var_list[Source.SPICE] = spice_list

    run_state.nows_template_filename = template_path.with_name('nows_' + Path(template).name)
    write_nows_template(run_state.nows_template_filename, vm_nows)

    return {Source.PDS3: label_list, Source.FITS: fits_list, Source.SPICE: spice_list}

def find_vars(pattern: str, template: str, groups=[1]) -> list:
    """ Utility for handling regex search of template for variable pointers. """
    var_list = []
    for match in re.compile(pattern).finditer(template):
        var_parts = []
        for g in groups:
            var_parts.append(match.group(g))

        if len(var_parts) == 1:
            #only 1 group for PDS3 and SPICE variables
            var_parts = var_parts[0]
        else:
            #groups 1 and 2 store extension and keyword for FITS variables
            var_parts = tuple(var_parts)

        var_list.append(var_parts)

    return var_list

def build_nows_template(line: str, vm_nows: str, current_line: str, in_velocity: bool) -> tuple[str, str, bool]:
    """ For human-readability, users may create templates with lots of whitespace. This function constructs a string of the template whitespace removed so the output looks like nice xml. """
    open_char = ['(', '{', '[']
    close_char = [')', '}', ']']

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
    
    return vm_nows, current_line, in_velocity

def write_nows_template(nows_temeplate_path: Path, vm_nows: str) -> Path:
    """ Utility to write the no whitespace (nows) template file """
    nows_temeplate_path.write_text(vm_nows)