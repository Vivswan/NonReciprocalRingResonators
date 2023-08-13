from __future__ import annotations

import sys
from pathlib import Path
from typing import Union, Dict

from out.results import get_results_path
from src.functions.param_to_combinations import param_to_combinations
from src.functions.process_scripts import process_scripts


def run_point(
        parameters: Dict[str, float],
        setup_script: str,
        script_name: str,
        hide: bool = True,
        location: Union[str, Path] = Path(sys.argv[0]).expanduser().absolute()
) -> None:
    import lumapi
    _, script = process_scripts(
        parameters=parameters,
        location=location,
        setup_script=setup_script,
        script_name=script_name,
    )

    with lumapi.INTERCONNECT(hide=hide) as interconnect:
        interconnect.eval(script)


def run_sweep(
        parameters: Dict[str, Dict[str, Union[int, float]]],
        setup_script: str,
        script_name: str,
        hide: bool = True
):
    location = get_results_path().joinpath(script_name)
    location.mkdir(exist_ok=True, parents=True)

    for i in param_to_combinations(parameters):
        run_point(
            parameters=i,
            setup_script=setup_script,
            script_name=script_name,
            hide=hide
        )
