from __future__ import annotations

import argparse
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
    center_wavelength = {wavelength};
    wavelength_gap = {wavelength_gap};
    
    laser_power = {power};
    insertion_loss = {insertion_loss};
    n_eff = {n_eff};
    n_grp = {n_grp};
    
    # -1 for non-reciprocal, 0 for reciprocal and +1 for full-reciprocal
    reciprocal = {reciprocal};
    laser_sweep = {laser_sweep};
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
        help='Components to sweep, format: "[i|w|d]:<component_name>:<parameter_name>:<min>:<max>:<num>"'
    )
    parsed_args.add_argument('-n', '--num-resonators', type=int, default=3, help='Number of resonators')
    parsed_args.add_argument('-w', '--wavelength', type=float, default=1550, help='Center wavelength (nm)')
    parsed_args.add_argument('-g', '--wavelength-gap', type=float, default=100, help='Wavelength gap (nm)')
    parsed_args.add_argument('-p', '--laser-power', type=float, default=0.001, help='Laser Power (W)')
    parsed_args.add_argument('-i', '--insertion-loss', type=float, default=0, help='Insertion loss (dB/cm)')
    parsed_args.add_argument('-e', '--n-eff', type=float, default=2.262, help='Effective index')
    parsed_args.add_argument('-r', '--n-grp', type=float, default=3.484, help='Group index')
    parsed_args.add_argument('-o', '--reciprocal', type=int, default=0, help='Reciprocal (0, 1 or -1)')
    parsed_args.add_argument('-l', '--laser-sweep', action="store_true", help='Sweep wavelength')
    parsed_args.add_argument('-a', '--waveguides', action="store_true", help='with waveguides')
    parsed_args.add_argument('-r', '--run', action="store_true", help='Run simulation')
    parsed_args.add_argument('-l', '--lsf', action="store_true", help='Create LSF script')
    parsed_args.add_argument('-g', '--gui', action="store_true", help='Run with GUI, --run only')
    parsed_args.add_argument('-s', '--slurm', action="store_true", help='with SLURM, --lsf only')
    parsed_args = parsed_args.parse_args(*args, **kwargs)

    if parsed_args.run and parsed_args.lsf:
        raise ValueError('Cannot run both run and lsf')

    if not parsed_args.run and not parsed_args.lsf:
        raise ValueError('Must run either run or lsf')

    hash_args = {
        'components': sorted([i.split(":")[:3] for i in parsed_args.components]),
        'num_resonators': parsed_args.num_resonators,
        'wavelength': parsed_args.wavelength,
        'wavelength_gap': parsed_args.wavelength_gap,
        'power': parsed_args.power,
        'insertion_loss': parsed_args.insertion_loss,
        'n_eff': parsed_args.n_eff,
        'n_grp': parsed_args.n_grp,
        'reciprocal': parsed_args.reciprocal,
        'laser_sweep': parsed_args.laser_sweep,
        'waveguides': parsed_args.waveguides,
    }
    hash_name = sha256(json.dumps(hash_args, sort_keys=True).encode("utf-8")).hexdigest()[:HASH_LENGTH]
    script_name = f'simulation_{hash_name}'
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
                'Invalid component format, must be "[l|d]:<component_name>*:<parameter_name>*:<min>:<max>:<num>"'
            )

        component = {
            'type': component[0].split('|'),
            'component_name': component[1].split('|'),
            'parameter_name': component[2].split('|'),
            'min': float(component[3]),
            'max': float(component[4]),
            'num': int(component[5]),
        }

        if not all(i in ['i', 'w', 'd'] for i in component['type']):
            raise ValueError(f'Invalid component type {component["type"]!r}, must be "i", "w" or "d"')

        components.append(component)
        parameter_name = sha256(
            json.dumps((component['type'], component['component_name'], component['parameter_name'])).encode("utf-8")
        ).hexdigest()[:HASH_LENGTH]
        parameters[parameter_name] = {
            'min': float(component['min']),
            'max': float(component['max']),
            'num': int(component['num']),
        }

        absolute_components = []
        if 'i' in component['type']:
            for i in range(1, parsed_args.matrix_size + 1):
                absolute_components.append(f"::Root Element::L_{i}_0")
        if 'w' in component['type']:
            for i in range(1, parsed_args.matrix_size + 1):
                absolute_components.append(f"::Root Element::L_0_{i}")
        if 'd' in component['type']:
            for i in range(1, parsed_args.matrix_size + 1):
                for j in range(1, parsed_args.matrix_size + 1):
                    absolute_components.append(f"::Root Element::D_{i}_{j}")

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
