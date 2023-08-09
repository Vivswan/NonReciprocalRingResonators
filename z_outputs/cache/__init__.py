from pathlib import Path


def get_cache_path():
    return Path(__file__).expanduser().absolute().parent


def clear_cache():
    for file in get_cache_path().glob("*.json"):
        file.unlink()
    for file in get_cache_path().glob("*.pkl"):
        file.unlink()
