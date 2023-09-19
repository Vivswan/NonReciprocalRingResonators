from __future__ import annotations

import json
import os
from hashlib import sha256
from pathlib import Path
from typing import Union, Dict, Tuple, Optional

from out.results import get_results_path
from src.functions.__const__ import HASH_LENGTH
from src.lsf_scripts import get_lsf_scripts_path

START_SCRIPT = r'''
    addpath("{lsf_scripts_path}");
    autosaveoff;
    switchtodesign;
    groupscope("::Root Element");
    deleteall;
    if (exist("preserve_me")) {
        clearexcept(preserve_me);
    } else {
        clear;
    }
    clearfunctions;

    main__ = "python";
    setnamed("::Root Element", "bitrate", 2.5e+10);
    setnamed("::Root Element", "time window", 5e-9);
    setnamed("::Root Element", "sample rate", 2e+12);
'''

PRE_RUN_SAVE_SCRIPT = r'''
    # exportnetlist("{results_path}/{name}.spi");
'''

RUN_SCRIPT = r'''
    save("{results_path}/{name}.ipc");
    run;
    save("{results_path}/{name}.ipc");
'''

POST_RUN_SAVE_SCRIPT = r'''
    save_properties_results;
    results = get_all_results();
    properties = get_all_element_properties("");
    matlabsave("{results_path}/{name}.mat", results, properties);
'''

END_SCRIPT = r'''
    switchtodesign;
    groupscope("::Root Element");
    deleteall;
    if (exist("preserve_me")) {
        clearexcept(preserve_me);
    } else {
        clear;
    }
    clearfunctions;

    save("{results_path}/{name}.ipc");
    write("{results_path}/{name}.completed.txt", "completed", "overwrite");
    # exit;
'''


def get_relative_path(path1: Union[str, Path], path2: Union[str, Path]) -> str:
    path1 = Path(path1).expanduser().absolute()
    path2 = Path(path2).expanduser().absolute()
    common_path = Path(os.path.commonpath([path1, path2]))
    path1_to_common = path1.relative_to(common_path)
    path2_to_common = path2.relative_to(common_path)
    path1_to_common = Path("/".join([".."] * len(path1_to_common.parts)))
    path2_to_common = Path("/".join(path2_to_common.parts))
    return str(path1_to_common / path2_to_common).replace("\\", "/")


def process_scripts(
        parameters: Dict[str, float],
        location: Union[Path, str],
        setup_script: str,
        script_name: str,
        index: Optional[Union[str, int]] = None,
) -> Tuple[str, str]:
    parameters = [(k, v if isinstance(v, str) else f"{v:.12f}") for k, v in parameters.items()]
    parameters = {k: v for k, v in parameters if v is not None}
    point_str = sha256(json.dumps(parameters, sort_keys=True).encode("utf-8")).hexdigest()[:HASH_LENGTH]
    if index is None:
        name = f'{script_name}_{point_str}'
    else:
        name = f'{script_name}_{index}_{point_str}'

    scripts = [START_SCRIPT, setup_script, PRE_RUN_SAVE_SCRIPT, RUN_SCRIPT, POST_RUN_SAVE_SCRIPT, END_SCRIPT]

    for i in range(len(scripts)):
        scripts[i] = scripts[i].replace("{script_name}", script_name)
        scripts[i] = scripts[i].replace("{lsf_scripts_path}", get_relative_path(location, get_lsf_scripts_path()))
        scripts[i] = scripts[i].replace("{results_path}", get_relative_path(location, get_results_path() / script_name))
        scripts[i] = scripts[i].replace("{name}", name)
        for k, v in parameters.items():
            scripts[i] = scripts[i].replace(f"{{{k}}}", v)

    return name, "\n".join(scripts)
