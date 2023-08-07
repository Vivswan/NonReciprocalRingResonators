import copy
import pickle
from hashlib import sha256
from pathlib import Path
from typing import Sequence, Optional, Callable

import numpy as np

from src.compile_data import load_data
from src.functions.__const__ import HASH_LENGTH
from src.plot_scripts._extract import extract
from z_outputs.cache import get_cache_path


def db_to_watts(db):
    if isinstance(db, Sequence):
        return [db_to_watts(x) for x in db]

    return 10 ** ((db - 30) / 10)


def min_max(value):
    results = []
    for x in value:
        if isinstance(x, Sequence):
            min_section = len(x) // 4
            x = x[min_section:-min_section]
        results.append((np.min(x), np.max(x)))
    return np.array(results)


def get_parameter(location, parameter_loc, force=False):
    location = Path(location)
    cache_file = location.stem + "_" + sha256(parameter_loc.encode("utf-8")).hexdigest()[:HASH_LENGTH] + ".pkl"

    if get_cache_path().joinpath(cache_file).exists() and not force:
        value = pickle.load(get_cache_path().joinpath(cache_file).open("rb"))
        print(f"Loaded {parameter_loc!r} from {cache_file!r}")
    else:
        print(f"Loading {parameter_loc!r} from {str(location)!r}")
        with load_data(location=location) as data:
            value = extract(data, *parameter_loc.format(i=1).split("|"))
        pickle.dump(value, get_cache_path().joinpath(cache_file).open("wb"))
        print(f"Saved {parameter_loc!r} in {cache_file!r}")

    return value


def get_parameters(location, parameters, force):
    parameters = copy.deepcopy(parameters)
    for k, v in parameters.items():
        if k.startswith("_"):
            continue

        if not isinstance(v, tuple):
            v = (v, None)

        parameter_loc: str = v[0]
        parameter_func: Optional[Callable] = v[1]
        value = get_parameter(location, parameter_loc, force)

        if parameter_func is not None:
            value = parameter_func(value)

        parameters[k] = value

    return parameters
