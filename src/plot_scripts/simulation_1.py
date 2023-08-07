import pickle
from hashlib import sha256
from pathlib import Path
from typing import Sequence

import numpy as np
from matplotlib import pyplot as plt

from src.functions.__const__ import HASH_LENGTH
from src.plot_scripts.common import db_to_watts, min_max, get_parameters
from z_outputs.cache import get_cache_path
from z_outputs.plots import get_plots_path
from z_outputs.results import get_results_path


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
    print(f"Plotting {location.stem}")
    location = Path(location)
    is_reciprocal = location.stem.split("_")[1][1] != "0"
    parameters = {
        "coupling": "properties|::Root Element::R_1|coupling",
        "t_1": "results|::Root Element::OSA_R_1_rt|mode 1/signal|values",
        "t_2": f"results|::Root Element::OSA_R_1_{'lb' if is_reciprocal else 'rb'}|mode 1/signal|values",
        "f_1": "results|::Root Element::OSA_R_1_rt|mode 1/signal|Frequency",
        "f_2": f"results|::Root Element::OSA_R_1_{'lb' if is_reciprocal else 'rb'}|mode 1/signal|Frequency",
    }

    parameters = get_parameters(location, parameters, force)

    for i in np.linspace(0, len(parameters["f_1"]) - 1, n, dtype=int):
        fig, ax = plt.subplots(1, 1)
        ax.plot(parameters["f_1"][i], parameters["t_1"][i], label="Signal 1")
        ax.plot(parameters["f_2"][i], parameters["t_2"][i], label="Signal 2")
        ax.set_xlabel("Frequency (THz)")
        ax.set_ylabel("Signal (dBm)")
        ax.set_title(f"Simulation 1: {location.stem}\n{parameters['coupling'][i]:.3f} coupling")
        ax.legend()
        plt.tight_layout()
        plt.savefig(get_plots_path() / f"{location.stem}_frequency_{i}.png", dpi=600)
        plt.show()
        plt.close(fig)


if __name__ == '__main__':
    basepath = get_results_path()
    # basepath = Path(r"/scratch/slurm-2039166")
    simulation_1_transmission(basepath / "simulation_10110_7806f8af.sqlite")
    simulation_1_transmission(basepath / "simulation_11110_7806f8af.sqlite")
    simulation_1_transmission(basepath / "simulation_12110_7806f8af.sqlite")
    simulation_1_frequency(basepath / "simulation_10110_7806f8af.sqlite")
    simulation_1_frequency(basepath / "simulation_11110_7806f8af.sqlite")
    simulation_1_frequency(basepath / "simulation_12110_7806f8af.sqlite")
