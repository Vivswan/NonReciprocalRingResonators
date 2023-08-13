from pathlib import Path

PROXY_CACHE_LOCATION = None


def get_cache_path():
    if PROXY_CACHE_LOCATION is not None:
        return PROXY_CACHE_LOCATION

    return Path(__file__).expanduser().absolute().parent


def set_cache_path(proxy_cache_location):
    global PROXY_CACHE_LOCATION
    PROXY_CACHE_LOCATION = Path(proxy_cache_location).expanduser().absolute()
    PROXY_CACHE_LOCATION.mkdir(parents=True, exist_ok=True)


def clear_cache():
    for file in get_cache_path().glob("*.json"):
        file.unlink()
    for file in get_cache_path().glob("*.pkl"):
        file.unlink()
