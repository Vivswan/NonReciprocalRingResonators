import copy
import os
from pathlib import Path
import pickle
from hashlib import sha256
from typing import Sequence, Callable, Optional

import numpy as np
from matplotlib import pyplot as plt

from src.compile_data import load_data
from src.functions.__const__ import HASH_LENGTH
from src.plot_scripts._extract import extract
from z_outputs.cache import get_cache_path
from z_outputs.plots import get_plots_path
from z_outputs.results import get_results_path


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


def simulation_1_transmission(location, force=False):
    location = Path(location)
    parameters = {
        "coupling": "properties|::Root Element::R_1|coupling",
        "transmission": ("results|::Root Element::OSA_R_1_rt|mode 1/signal|values", min_max),
    }

    hash_str = [(k, v[0] if isinstance(v, Sequence) else v) for k, v in parameters.items()]
    hash_str = str(sorted(hash_str))
    full_cache_file = location.stem + "_" + sha256(hash_str.encode("utf-8")).hexdigest()[:HASH_LENGTH] + ".pkl"
    if get_cache_path().joinpath(full_cache_file).exists() and not force:
        parameters = pickle.load(get_cache_path().joinpath(full_cache_file).open("rb"))
    else:
        parameters = get_parameters(location, parameters, force)
        pickle.dump(parameters, get_cache_path().joinpath(full_cache_file).open("wb"))
        print(f"Saved {full_cache_file}")

    fig, ax = plt.subplots(1, 1)
    parameters["T"] = db_to_watts(parameters["transmission"]) * 1e3
    parameters["T_min"] = parameters["T"][:, 0]
    parameters["T_max"] = parameters["T"][:, 1]
    parameters["t"] = 1 - parameters["coupling"]

    ax.scatter(parameters["t"], parameters["T_min"], s=1, label="min")
    ax.scatter(parameters["t"], parameters["T_max"], s=1, label="max")
    ax.set_xlabel("t")
    ax.set_ylabel("T")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(f"Simulation 1\n{location.stem}")
    ax.legend()
    plt.tight_layout()
    plt.savefig(get_plots_path() / f"{location.stem}_transmission.png", dpi=600)
    plt.show()
    plt.close(fig)


def simulation_1_frequency(location, n=10, force=False):
    location = Path(location)
    parameters = {
        "coupling": "properties|::Root Element::R_1|coupling",
        "transmission": "results|::Root Element::OSA_R_1_rt|mode 1/signal|values",
        "frequency": "results|::Root Element::OSA_R_1_rt|mode 1/signal|Frequency",
    }

    parameters = get_parameters(location, parameters, force)

    for i in np.linspace(0, len(parameters["frequency"]) - 1, n, dtype=int):
        fig, ax = plt.subplots(1, 1)
        ax.plot(parameters["frequency"][i], parameters["transmission"][i])
        ax.set_xlabel("Frequency (THz)")
        ax.set_ylabel("Transmission (W)")
        ax.set_title(f"Simulation 1\n{location.stem}\n{parameters['coupling'][i]:.3f} coupling")
        plt.tight_layout()
        plt.savefig(get_plots_path() / f"{location.stem}_frequency_{i}.png", dpi=600)
        plt.show()
        plt.close(fig)


if __name__ == '__main__':
    basepath = get_results_path()
    # basepath = Path(r"/scratch/slurm-2039072")
    simulation_1_transmission(basepath / "simulation_10110_7806f8af.sqlite")
    simulation_1_transmission(basepath / "simulation_11110_7806f8af.sqlite")
    simulation_1_transmission(basepath / "simulation_12110_7806f8af.sqlite")
    simulation_1_frequency(basepath / "simulation_10110_7806f8af.sqlite")
    simulation_1_frequency(basepath / "simulation_11110_7806f8af.sqlite")
    simulation_1_frequency(basepath / "simulation_12110_7806f8af.sqlite")
