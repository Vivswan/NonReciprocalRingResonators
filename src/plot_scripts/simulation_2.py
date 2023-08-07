from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt

from src.plot_scripts.common import get_parameters
from z_outputs.plots import get_plots_path
from z_outputs.results import get_results_path


def simulation_2(location, n=10, force=False):
    print(f"Plotting {location.stem}")
    location = Path(location)
    is_reciprocal = location.stem.split("_")[1][1] != "0"
    parameters = {
        "coupling": "properties|::Root Element::R_1|coupling",
        "phase": "properties|::Root Element::R_1|phase",
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
        ax.set_title(f"Simulation 1: {location.stem}\n{parameters['coupling'][i]:.3f} coupling, {parameters['phase'][i]:.3f} phase")
        ax.legend()
        plt.tight_layout()
        plt.savefig(get_plots_path() / f"{location.stem}_frequency_{i}.png", dpi=600)
        plt.show()
        plt.close(fig)


if __name__ == '__main__':
    basepath = get_results_path()
    basepath = Path(r"/scratch/slurm-2039166")
    simulation_2(basepath / "simulation_10110_868d1548.sqlite")
    simulation_2(basepath / "simulation_11110_868d1548.sqlite")
