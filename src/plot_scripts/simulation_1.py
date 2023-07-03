import pickle
from hashlib import sha256

from matplotlib import pyplot as plt

from src.compile_data import load_data
from src.functions.__const__ import HASH_LENGTH
from src.plot_scripts._extract import extract
from z_outputs.cache import get_cache_path
from z_outputs.plots import get_plots_path


def db_to_watts(db):
    return 10 ** ((db - 30) / 10)


def simulation_1(name, force=False):
    parameters = {
        "coupling": "properties|::Root Element::R_1|coupling",
        "transmission": ("results|::Root Element::OSA_R_1_rt|mode 1/signal|values", db_to_watts),
        "frequency": ("results|::Root Element::OSA_R_1_rt|mode 1/signal|Frequency", db_to_watts),
    }
    for k, v in parameters.items():
        if k.startswith("_"):
            continue
        if not isinstance(v, tuple):
            v = (v, None)

        cache_file = name + "_" + sha256(v[0].encode("utf-8")).hexdigest()[:HASH_LENGTH] + ".pkl"
        if get_cache_path().joinpath(cache_file).exists() and not force:
            value = pickle.load(get_cache_path().joinpath(cache_file).open("rb"))
            print(f"Loaded {cache_file}")
        else:
            with load_data(name) as data:
                value = extract(data, *v[0].format(i=1).split("|"))
            pickle.dump(value, get_cache_path().joinpath(cache_file).open("wb"))

        parameters[k] = (value, v[1])

    fig, ax = plt.subplots(1, 1)
    plt.tight_layout()
    plt.savefig(get_plots_path() / f"{name}.png", dpi=1200)
    plt.show()


if __name__ == '__main__':
    # simulation_1("simulation_10010_107ac0a2")
    simulation_1("simulation_11010_107ac0a2")
    # simulation_1("simulation_12010_107ac0a2")
