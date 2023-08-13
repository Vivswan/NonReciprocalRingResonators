from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional, Union, Dict

from out.lsf import get_lsf_path
from out.results import get_results_path
from src.compile_data import get_compile_data_path
from src.functions.param_to_combinations import param_to_combinations
from src.functions.process_scripts import process_scripts
from src.lsf_scripts import get_lsf_scripts_path


def create_lsf_script(
        parameters: Dict[str, float],
        setup_script: str,
        script_name: str,
        index: Optional[Union[str, int]] = None,
        location: Union[str, Path] = get_lsf_path()
) -> Path:
    location = Path(location).expanduser().absolute()
    name, script = process_scripts(
        parameters=parameters,
        location=location,
        setup_script=setup_script,
        script_name=script_name,
        index=index,
    )

    script_path = location.joinpath(name + ".run.lsf")
    script_path.write_text(script, encoding="utf-8")
    return script_path


def create_lsf_script_sweep(
        parameters: Dict[str, Dict[str, Union[int, float]]],
        setup_script: str,
        script_name: str,
        location: Optional[Union[str, Path]] = None,
        data_location: Optional[Union[str, Path]] = None,
        with_slurm: bool = True,
):
    location = get_lsf_path() if location is None else Path(location).expanduser().absolute()
    data_location = get_results_path() if data_location is None else Path(data_location).expanduser().absolute()

    location = location.joinpath(script_name).absolute()
    data_location = data_location.joinpath(script_name).absolute()

    if location.exists():
        for file in location.iterdir():
            if file.is_file():
                file.unlink()
            else:
                shutil.rmtree(file)

    location.mkdir(exist_ok=True)
    data_location.mkdir(exist_ok=True)
    location_str = str(location).replace("\\", "/")
    data_location_str = str(data_location).replace("\\", "/")
    compile_data_py_str = str(get_compile_data_path()).replace("\\", "/")

    files = {}
    for i, parameter in enumerate(param_to_combinations(parameters)):
        files[i] = create_lsf_script(
            parameters=parameter,
            setup_script=setup_script,
            script_name=script_name,
            index=str(i).zfill(5),
            location=location
        )

    if not with_slurm:
        return files

    slurm_lsf = get_lsf_scripts_path().joinpath("lsf.slurm").read_text(encoding="utf-8")
    slurm_lsf = slurm_lsf.replace("@name@", f"{script_name}")
    slurm_lsf = slurm_lsf.replace("@RunDirectoryLocation@", location_str)
    slurm_lsf = slurm_lsf.replace("@DataDirectoryLocation@", data_location_str)
    location.joinpath(f"{script_name}.lsf.slurm").write_text(slurm_lsf, encoding="utf-8")

    slurm_compile = get_lsf_scripts_path().joinpath("compile.slurm").read_text(encoding="utf-8")
    slurm_compile = slurm_compile.replace("@name@", f"{script_name}_compile")
    slurm_compile = slurm_compile.replace("@RunDirectoryLocation@", location_str)
    slurm_compile = slurm_compile.replace("@DataDirectoryLocation@", data_location_str)
    slurm_compile = slurm_compile.replace("@compile_data_py@", compile_data_py_str)
    location.parent.joinpath(f"{script_name}.compile.slurm").write_text(slurm_compile, encoding="utf-8")

    lsf_script = get_lsf_scripts_path().joinpath("sbatch.lsf").read_text(encoding="utf-8")
    lsf_script = lsf_script.replace("@name@", f"{script_name}")
    lsf_script = lsf_script.replace("@RunDirectoryLocation@", location_str)
    lsf_script = lsf_script.replace("@DataDirectoryLocation@", data_location_str)
    lsf_script = lsf_script.replace("@compile_data_py@", compile_data_py_str)
    location.joinpath(f"{script_name}.sbatch.lsf").write_text(lsf_script, encoding="utf-8")
    return files
