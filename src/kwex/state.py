from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class RunState:
    """ Class that contains persistent state values that need to be accessed and modified across entire program. """
    output_list: list[Path] = field(default_factory=list)
    bad_output_list: set[Path] = field(default_factory=set)
    json_list: list[Path] = field(default_factory=list)

    spice_eqns: dict = field(default_factory=dict)
    body_frames: dict = field(default_factory=dict)
    fits_spice_kws: dict = field(default_factory=dict)
    instr_frame_params: dict = field(default_factory=dict)
    var_sub_list: dict = field(default_factory=dict)

    nows_template_str: str = ''
    abcorr: str = ''

    input_root: Path = Path()
    kernel_path: Path = Path()
    nows_template_filename: Path = Path()

    bad_output: bool = False
    java_compile_process: bool = False
    velocity_process: bool = False
    temp_kernel: bool = False

run_state = RunState()
