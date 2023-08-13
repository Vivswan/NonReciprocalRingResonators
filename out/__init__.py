from pathlib import Path


def get_output_path():
    return Path(__file__).expanduser().absolute().parent
