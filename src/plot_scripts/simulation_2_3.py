from pathlib import Path
from typing import Sequence

import numpy as np
from matplotlib import pyplot as plt

from out.cache import get_cache_path
from out.plots import get_plots_path
from out.results import get_results_path
from src.plot_scripts.common import get_parameters


def simulation_2_er(location, force=False):
    print(f"Plotting {location.stem}")
    location = Path(location)
    is_reciprocal = location.stem.split("_")[3][1] != "0"
    print(f"is_reciprocal: {is_reciprocal}")
    parameters = {
        "coupling": "properties|::Root Element::R_1|coupling",
        "phase": "properties|::Root Element::R_1|phase",
        "t_1": "results|::Root Element::OSA_R_1_rt|mode 1/signal|values",
        "t_2": f"results|::Root Element::OSA_R_1_{'lb' if is_reciprocal else 'rb'}|mode 1/signal|values",
        "f_1": "results|::Root Element::OSA_R_1_rt|mode 1/signal|Frequency",
        "f_2": f"results|::Root Element::OSA_R_1_{'lb' if is_reciprocal else 'rb'}|mode 1/signal|Frequency",
    }

    parameters = get_parameters(location, parameters, force)

    phi_shift = (np.pi / 2) if is_reciprocal else (np.pi / 4)
    phi_limits = (0, np.pi) if is_reciprocal else (-np.pi / 2, np.pi / 2)

    all_phases = np.unique(parameters["phase"])
    using_phi_shift = all_phases[np.argmin(np.abs(all_phases - phi_shift))]
    print(f"Phase range: [{np.min(all_phases)}, {np.max(all_phases)}]")
    print(f"Using phase shift: {using_phi_shift}")

    coupling = 0.1
    all_coupling = np.unique(parameters["coupling"])
    using_coupling = all_coupling[np.argmin(np.abs(all_coupling - coupling))]
    coupling_phi_index = \
        np.where((parameters["coupling"] == using_coupling) & (parameters["phase"] == using_phi_shift))[0][0]
    print(f"Coupling range: [{np.min(all_coupling)}, {np.max(all_coupling)}]")
    print(f"Using coupling: {using_coupling}")
    print(f"Using coupling_phi_index: {coupling_phi_index}")

    frequency = 3e8 / 1550e-9
    signal_1_on_index = np.array(parameters["t_1"][coupling_phi_index])
    freq_on_index = np.array(parameters["f_1"][coupling_phi_index])
    peaks = np.where(signal_1_on_index < (np.min(signal_1_on_index) * 0.9))[0]
    freq_of_peaks = freq_on_index[peaks]
    using_freq = freq_of_peaks[np.argmin(np.abs(freq_of_peaks - frequency))]
    freq_index = peaks[np.argmin(np.abs(freq_of_peaks - frequency))]
    print(f"Using frequency (probe at): {3e8 * 1e9 / using_freq:.3f} nm or {using_freq * 1e-12:.3f} THz")
    print(f"Using index: {freq_index}")

    fig, ax = plt.subplots(1, 1)
    ax.plot(parameters["f_1"][coupling_phi_index], parameters["t_1"][coupling_phi_index], label="Signal 1")
    ax.plot(parameters["f_2"][coupling_phi_index], parameters["t_2"][coupling_phi_index], label="Signal 2")
    ax.set_xlabel("Frequency (THz)")
    ax.set_ylabel("Signal (dBm)")
    ax.set_title(
        f"Simulation 2: {location.stem}\n"
        f"{parameters['coupling'][coupling_phi_index]:.3f} coupling, "
        f"{parameters['phase'][coupling_phi_index]:.3f} phase"
    )
    ax.legend()
    plt.tight_layout()
    plt.savefig(
        get_plots_path() / f"{location.stem}_frequency_{int(coupling * 10)}_{int(using_phi_shift * 10 / np.pi)}.png",
        dpi=600
    )
    plt.show()
    plt.close(fig)

    if isinstance(parameters["t_1"], np.ndarray):
        parameters["t_1"] = parameters["t_1"].tolist()
    if isinstance(parameters["t_2"], np.ndarray):
        parameters["t_2"] = parameters["t_2"].tolist()

    er_p = np.array([np.nan] * len(parameters["coupling"]))
    for i in range(len(parameters["coupling"])):
        if not isinstance(parameters["t_1"][i], Sequence):
            continue
        if not isinstance(parameters["t_2"][i], Sequence):
            continue
        er_p[i] = parameters["t_1"][i][freq_index] - parameters["t_2"][i][freq_index]

    fig, ax = plt.subplots(1, 1)
    sc = ax.scatter(parameters["phase"] / np.pi, parameters["coupling"], c=er_p)
    cbar = plt.colorbar(sc)
    cbar.set_label("ER")
    ax.set_xlabel("Phase (pi)")
    ax.set_ylabel("Coupling")
    ax.set_title(f"Simulation 2: {location.stem}")
    ax.set_xlim(phi_limits[0] / np.pi, phi_limits[1] / np.pi)
    plt.tight_layout()
    plt.savefig(get_plots_path() / f"{location.stem}_er.png", dpi=600)
    plt.show()
    plt.close(fig)

    for i in range(int(np.min(parameters["coupling"]) * 10), int(np.max(parameters["coupling"]) * 10) + 1):
        plot_coupling = i / 10
        fig, ax = plt.subplots(1, 1)
        with_coupling = all_coupling[np.argmin(np.abs(all_coupling - plot_coupling))]
        indexes = parameters["coupling"] == with_coupling
        ax.plot(parameters["phase"][indexes] / np.pi, er_p[indexes])
        ax.set_xlabel("Phase (pi)")
        ax.set_ylabel("ER")
        ax.set_title(f"Simulation 2: {location.stem}; \n {with_coupling:.3f} coupling")
        ax.set_xlim(phi_limits[0] / np.pi, phi_limits[1] / np.pi)
        plt.tight_layout()
        plt.savefig(get_plots_path() / f"{location.stem}_er_{int(with_coupling * 10)}.png", dpi=600)
        plt.show()
        plt.close(fig)


if __name__ == '__main__':
    basepath = get_results_path()
    # slurm_id = 2041249
    # basepath = Path(rf"/scratch/slurm-{slurm_id}")
    # set_cache_path(Path(rf"/scratch/slurm-{slurm_id}/cache"))
    print(f"basepath: {basepath}")
    print(f"get_cache_path: {get_cache_path()}")
    simulation_2_er(basepath / "simulation_2_868d1548_10110.sqlite")
    simulation_2_er(basepath / "simulation_2_868d1548_11110.sqlite")
    simulation_2_er(basepath / "simulation_3_868d1548_10110.sqlite")
    simulation_2_er(basepath / "simulation_3_868d1548_11110.sqlite")
