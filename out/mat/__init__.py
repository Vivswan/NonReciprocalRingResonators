from pathlib import Path


def get_mat_path():
    return Path(__file__).expanduser().absolute().parent
