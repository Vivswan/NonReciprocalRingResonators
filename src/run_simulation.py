from __future__ import annotations

import argparse
import copy
import itertools
import json
from hashlib import sha256
from typing import Union, Dict, List

from src.functions.__const__ import HASH_LENGTH
from src.functions.lsf_script import create_lsf_script_sweep
from src.functions.run_sim import run_sweep
from z_outputs import get_output_path

SETUP_SCRIPT = r'''
    num_resonators = {num_resonators};
    center_wavelength = {wavelength} * 1e-9; # m
    wavelength_gap = {wavelength_gap} * 1e-9; # m
    
    laser_power = {laser_power} * 1e-3; # W
    wg_insertion_loss = {wg_insertion_loss}; # dB/cm
    dc_insertion_loss = {dc_insertion_loss}; # dB
    bend_insertion_loss = {bend_insertion_loss}; # dB/2pi
    straight_waveguide_length = {straight_waveguide_length} * 1e-6; # m
    straight_n_eff = {straight_n_eff};
    straight_n_grp = {straight_n_grp};
    bend_n_eff = {bend_n_eff};
    bend_n_grp = {bend_n_grp};
    
    # -1 for non-reciprocal, 0 for reciprocal and +1 for full-reciprocal
    reciprocal = {reciprocal};
    frequency_sweep = {frequency_sweep};
    waveguides = {waveguides};
    
    record_all = true;
    annotate_all = 3;

    addproperty("::Root Element", "simulation_of", "String", type="String");
    setnamed("::Root Element", "simulation_of", {simulation_of});
    simulation;

'''


def _main(*args, **kwargs):
    parsed_args = argparse.ArgumentParser(description='Run DPUC component sweep')

    parsed_args.add_argument(
        '-c', '--components', type=str, nargs='+', required=True,
        help='Components to sweep, format: "[r|c|s]:<component_name>:<parameter_name>:<min>:<max>:<num>"'
    )
    parsed_args.add_argument('-n', '--num-resonators', type=int, required=True, help='Number of resonators')
    parsed_args.add_argument('--wavelength', type=float, default=1550, help='Center wavelength (nm)')
    parsed_args.add_argument('--wavelength-gap', type=float, default=100, help='Wavelength gap (nm)')
    parsed_args.add_argument('--laser-power', type=float, default=1, help='Laser Power (mW)')
    parsed_args.add_argument('--wg-insertion-loss', type=float, default=3, help='Waveguide Insertion loss (dB/cm)')
    parsed_args.add_argument('--dc-insertion-loss', type=float, default=0.5, help='DC Insertion loss (dB)')
    parsed_args.add_argument('--bend-insertion-loss', type=float, default=0.04, help='Bend Insertion loss (dB/2pi)')
    parsed_args.add_argument('--straight-waveguide-length', type=float, default=100, help='Straight waveguide (nm)')
    parsed_args.add_argument('--straight-n-eff', type=float, default=2.262, help='Straight n_eff')
    parsed_args.add_argument('--straight-n-grp', type=float, default=3.484, help='Straight n_grp')
    parsed_args.add_argument('--bend-n-eff', type=float, default=2.262, help='Bend n_eff')
    parsed_args.add_argument('--bend-n-grp', type=float, default=3.484, help='Bend n_grp')
    parsed_args.add_argument('--reciprocal', type=int, required=True, help='Reciprocal (0, 1 or -1)')
    parsed_args.add_argument('--laser-sweep', action="store_true", help='Sweep wavelength')
    parsed_args.add_argument('--waveguides', action="store_true", help='with waveguides')
    parsed_args.add_argument('-r', '--run', action="store_true", help='Run simulation')
    parsed_args.add_argument('-l', '--lsf', action="store_true", help='Create LSF script')
    parsed_args.add_argument('-g', '--gui', action="store_true", help='Run with GUI, --run only')
    parsed_args.add_argument('-s', '--slurm', action="store_true", help='with SLURM, --lsf only')
    parsed_args = parsed_args.parse_args(*args, **kwargs)

    if parsed_args.run and parsed_args.lsf:
        raise ValueError('Cannot run both run and lsf')

    if not parsed_args.run and not parsed_args.lsf:
        raise ValueError('Must run either run or lsf')

    if parsed_args.num_resonators < 1:
        raise ValueError('Number of resonators must be positive')

    if parsed_args.reciprocal not in [-1, 0, 1]:
        raise ValueError('Reciprocal must be -1, 0 or 1')

    if parsed_args.wavelength_gap <= 0:
        raise ValueError('Wavelength gap must be positive')

    hash_args = copy.deepcopy(vars(parsed_args))
    # hash_args["components"] = sorted([i.split(":")[:3] for i in parsed_args.components])
    hash_args.pop('num_resonators')
    hash_args.pop('frequency_sweep')
    hash_args.pop('waveguides')
    hash_args.pop('run')
    hash_args.pop('lsf')
    hash_args.pop('gui')
    hash_args.pop('slurm')
    hash_name = sha256(json.dumps(hash_args, sort_keys=True).encode("utf-8")).hexdigest()[:HASH_LENGTH]
    script_name = (
        f'simulation_'
        f'{int(parsed_args.num_resonators)}'
        f'{int(parsed_args.frequency_sweep)}'
        f'{int(parsed_args.waveguides)}'
        f'_{hash_name}'
    )
    print(f"Script name: {script_name}")

    names_file = get_output_path() / f"names.json"
    names = json.loads(names_file.read_text()) if names_file.exists() else {}
    names[hash_name] = hash_args
    names_file.write_text(json.dumps(names, indent=4, sort_keys=True))

    setup_script = SETUP_SCRIPT
    setup_script = setup_script.replace('{matrix_size}', f"{parsed_args.matrix_size!r}")
    setup_script = setup_script.replace('{sweep_of}', f"{json.dumps(parsed_args.components)!r}")

    components: List[Dict[str, Union[str, float, int]]] = []
    parameters: Dict[str, Dict[str, Union[int, float]]] = {}
    for component in parsed_args.components:
        component = component.split(':')

        if len(component) != 6:
            raise ValueError(
                'Invalid component format, must be "[r|c|s]:<component_name>*:<parameter_name>*:<min>:<max>:<num>"'
            )

        component = {
            'type': component[0].split('|'),
            'component_name': component[1].split('|'),
            'parameter_name': component[2].split('|'),
            'min': float(component[3]),
            'max': float(component[4]) if len(component[4]) > 0 else None,
            'num': int(component[5]) if len(component[5]) > 0 else None,
        }

        if not all(i in ['r', 'c', 's'] for i in component['type']):
            raise ValueError(f'Invalid component type {component["type"]!r}, must be "r", "c" or "s"')

        if component['type'] == 's':
            if component['component_name']:
                root = "::Root Element::" + component['component_name']
            else:
                root = "::Root Element"
            parameter = component['parameter_name']
            parameter_value = component['min']
            setup_script += f'    setnamed("{root}", "{parameter}", {parameter_value});\n'

        components.append(component)
        parameter_name = sha256(
            json.dumps((component['type'], component['component_name'], component['parameter_name'])).encode("utf-8")
        ).hexdigest()[:HASH_LENGTH]
        parameters[parameter_name] = dict(min=component['min'], max=component['max'], num=component['num'])

        absolute_components = []
        if 'r' in component['type']:
            for i in range(1, parsed_args.num_resonators + 1):
                absolute_components.append(f"::Root Element::R_{i}")
        else:
            absolute_components.append(f"::Root Element")

        full_components = (absolute_components, component['component_name'], component['parameter_name'])
        combinations = itertools.product(*full_components)
        for root, name, parameter in combinations:
            root = f"{root}::{name}" if len(name) != 0 else f"{root}"
            setup_script += f'    setnamed("{root}", "{parameter}", {{{parameter_name}}});\n'

    common_args = dict(
        parameters=parameters,
        setup_script=setup_script,
        script_name=script_name,
    )

    if parsed_args.run:
        run_sweep(
            **common_args,
            hide=not parsed_args.gui,
        )
    elif parsed_args.lsf:
        create_lsf_script_sweep(
            **common_args,
            with_slurm=parsed_args.slurm,
        )


if __name__ == '__main__':
    _main()
