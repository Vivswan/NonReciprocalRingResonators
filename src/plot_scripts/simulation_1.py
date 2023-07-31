import pickle
from hashlib import sha256
from typing import Sequence

import numpy as np
from matplotlib import pyplot as plt

from src.compile_data import load_data
from src.functions.__const__ import HASH_LENGTH
from src.plot_scripts._extract import extract
from z_outputs.cache import get_cache_path
from z_outputs.plots import get_plots_path


def db_to_watts(db):
    if isinstance(db, (list, tuple)):
        return [db_to_watts(x) for x in db]

    return 10 ** ((db - 30) / 10)


def min_max(value):
    return np.array([(np.min(x), np.max(x)) for x in value])


def get_parameter(script_name, parameter_loc, force=False):
    cache_file = script_name + "_" + sha256(parameter_loc.encode("utf-8")).hexdigest()[:HASH_LENGTH] + ".pkl"
    if get_cache_path().joinpath(cache_file).exists() and not force:
        value = pickle.load(get_cache_path().joinpath(cache_file).open("rb"))
        print(f"Loaded {parameter_loc!r} from {cache_file!r}")
    else:
        with load_data(script_name) as data:
            value = extract(data, *parameter_loc.format(i=1).split("|"))
        pickle.dump(value, get_cache_path().joinpath(cache_file).open("wb"))
        print(f"Saved {parameter_loc!r} in {cache_file!r}")
    return value


def simulation_1_transmission(name, force=False):
    parameters = {
        "coupling": "properties|::Root Element::R_1|coupling",
        "transmission": ("results|::Root Element::OSA_R_1_rt|mode 1/signal|values", lambda x: db_to_watts(min_max(x))),
    }

    hash_str = [(k, v[0] if isinstance(v, Sequence) else v) for k, v in parameters.items()]
    hash_str = str(sorted(hash_str))
    full_cache_file = name + "_" + sha256(hash_str.encode("utf-8")).hexdigest()[:HASH_LENGTH] + ".pkl"
    if get_cache_path().joinpath(full_cache_file).exists():
        parameters = pickle.load(get_cache_path().joinpath(full_cache_file).open("rb"))
    else:
        for k, v in parameters.items():
            if k.startswith("_"):
                continue

            if not isinstance(v, tuple):
                v = (v, None)

            parameter_loc = v[0]
            parameter_func = v[1]
            value = get_parameter(name, parameter_loc, force)

            if parameter_func is not None:
                value = parameter_func(value)

            parameters[k] = value

        pickle.dump(parameters, get_cache_path().joinpath(full_cache_file).open("wb"))
        print(f"Saved {full_cache_file}")

    fig, ax = plt.subplots(1, 1)
    parameters["T"] = parameters["transmission"] * 1e3
    parameters["T_min"] = parameters["T"][:, 0]
    parameters["T_max"] = parameters["T"][:, 1]
    parameters["t"] = 1 - parameters["coupling"]
    parameters["ER"] = np.nan_to_num(parameters["T_max"] - parameters["T_min"])
    max_er_t = parameters["t"][np.argmax(parameters["ER"])]

    ax.scatter(parameters["t"], parameters["T_min"], s=1, label="min")
    ax.scatter(parameters["t"], parameters["T_max"], s=1, label="max")
    ax.scatter(parameters["t"], parameters["ER"], s=1, label="ER")
    ax.axvline(max_er_t, color="black", linestyle="--", label=f"max ER (t={max_er_t:.3f})")
    ax.set_xlabel("t")
    ax.set_ylabel("T")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(f"Simulation 1\n{name}")
    ax.legend()
    plt.tight_layout()
    plt.savefig(get_plots_path() / f"{name}_transmission.png", dpi=600)
    plt.show()


def simulation_1_frequency(name, n=10, force=False):
    parameters = {
        "coupling": "properties|::Root Element::R_1|coupling",
        "transmission": "results|::Root Element::OSA_R_1_rt|mode 1/signal|values",
        "frequency": "results|::Root Element::OSA_R_1_rt|mode 1/signal|Frequency",
    }

    for k, v in parameters.items():
        if k.startswith("_"):
            continue

        parameters[k] = get_parameter(name, v, force)

    for i in np.linspace(0, len(parameters["frequency"]) - 1, n, dtype=int):
        fig, ax = plt.subplots(1, 1)
        ax.plot(parameters["frequency"][i], parameters["transmission"][i])
        ax.set_xlabel("Frequency (THz)")
        ax.set_ylabel("Transmission (dB)")
        ax.set_title(f"Simulation 1\n{name}\n{parameters['coupling'][i]:.3f} coupling")
        plt.tight_layout()
        plt.savefig(get_plots_path() / f"{name}_frequency_{i}.png", dpi=600)
        plt.show()


if __name__ == '__main__':
    simulation_1_transmission("simulation_10110_7806f8af")
    simulation_1_transmission("simulation_11110_7806f8af")
    simulation_1_transmission("simulation_12110_7806f8af")
    simulation_1_frequency("simulation_10110_7806f8af")
    simulation_1_frequency("simulation_11110_7806f8af")
    simulation_1_frequency("simulation_12110_7806f8af")
