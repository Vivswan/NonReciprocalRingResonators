import argparse
from pathlib import Path

from src.plot_scripts.common import get_parameter
from z_outputs.cache import set_cache_path
from z_outputs.results import get_results_path

if __name__ == '__main__':
    parsed_args = argparse.ArgumentParser(description='Cache data from sqlite file')
    parsed_args.add_argument('name', type=str, required=True, help='Location of sqlite file')
    parsed_args.add_argument('parameter', type=str, required=True, help='Parameter to cache')
    parsed_args.add_argument('-l', '--location', type=str, default=None, help='Location of cache file')
    parsed_args.add_argument('-c', '--cache-location', type=str, default=None, help='Location of cache file')
    parsed_args.add_argument('-f', '--force', action='store_true', help='Force overwrite of cache file')
    args = parsed_args.parse_args()

    basepath = args.location if args.location is not None else get_results_path()
    basepath = Path(basepath).expanduser().absolute()
    if args.cache_location is not None:
        set_cache_path(args.cache_location)

    get_parameter(
        location=basepath.joinpath(args.name + '.sqlite'),
        parameter_loc=args.parameter,
        force=args.force,
    )
