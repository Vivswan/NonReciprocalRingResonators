from pathlib import Path


def get_results_path():
    return Path(__file__).expanduser().absolute().parent
