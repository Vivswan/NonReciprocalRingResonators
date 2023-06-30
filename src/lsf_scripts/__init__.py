from pathlib import Path


def get_lsf_scripts_path():
    return Path(__file__).expanduser().absolute().parent
