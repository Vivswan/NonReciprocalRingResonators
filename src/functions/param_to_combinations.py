from __future__ import annotations

from typing import Dict, Generator

import numpy as np


def param_to_combinations(parameters: Dict[str, Dict[str, float]]) -> Generator[Dict[str, float]]:
    if not parameters:
        yield {}
        return

    inputs_dict: Dict[str, np.ndarray] = {}

    for name, values in parameters.items():
        if "num" not in values:
            raise ValueError(f"Parameter {name} does not have a 'num' key")
        if "min" not in values:
            raise ValueError(f"Parameter {name} does not have a 'min' key")
        if "max" not in values:
            raise ValueError(f"Parameter {name} does not have a 'max' key")

        if values["num"] == 1:
            inputs_dict[name] = np.array([values["min"]])
        else:
            inputs_dict[name] = np.linspace(values["min"], values["max"], int(values["num"]))

    combinations = np.array(np.meshgrid(*inputs_dict.values())).T.reshape(-1, len(inputs_dict))

    for i in combinations:
        yield {name: float(value) for name, value in zip(inputs_dict.keys(), i)}
