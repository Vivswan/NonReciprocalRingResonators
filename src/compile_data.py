from __future__ import annotations

import argparse
import multiprocessing
import shutil
from functools import partial
from pathlib import Path
from typing import Union, Optional

import mat73
import numpy as np
import scipy
from tqdm import tqdm

from out.results import get_results_path
from src.functions.SqliteDeDuplicationDict import SqliteDeDuplicationDict


def get_compile_data_path():
    return Path(__file__).expanduser().absolute()


def refactor_lumerical_mat(data):
    if isinstance(data, dict):
        for k, v in data.items():
            data[k] = refactor_lumerical_mat(v)
        return data

    if isinstance(data, np.ndarray):
        return data.tolist()

    if isinstance(data, (str, int, float, bool)):
        return data

    if not isinstance(data, list):
        raise ValueError("Data must be a list")

    if len(data) == 1:
        return refactor_lumerical_mat(data[0])

    if len(data) == 2 and isinstance(data[0], list) and isinstance(data[0][0], str):
        return {refactor_lumerical_mat(data[0]): refactor_lumerical_mat(data[1])}

    if (
            len(data) == 3
            and isinstance(data[0][0], str)
            and isinstance(data[1][0], (list, np.ndarray, str, int, float, bool))
            and isinstance(data[2][0], dict)
    ):
        return {refactor_lumerical_mat(data[0]): {
            "values": refactor_lumerical_mat(data[1]),
            **refactor_lumerical_mat(data[2]),
        }}

    if (
            len(data) == 3
            and isinstance(data[0][0], str)
            and isinstance(data[1][0], (list, np.ndarray, str, int, float, bool))
            and isinstance(data[2][0], (list, np.ndarray, str, int, float, bool))
    ):
        return {refactor_lumerical_mat(data[0]): {
            "values": refactor_lumerical_mat(data[1]),
            "data": refactor_lumerical_mat(data[2]),
        }}

    for i in range(len(data)):
        data[i] = refactor_lumerical_mat(data[i])

    if all(isinstance(i, dict) for i in data):
        return {k: v for d in data for k, v in d.items()}

    return data


def mat_to_db(location: Union[str, Path], db_location: Optional[Union[str, Path]], delete: bool = False):
    location = Path(location).expanduser().absolute()
    with SqliteDeDuplicationDict(db_location) as db:
        if location.stem in db:
            return

        try:
            mat = mat73.loadmat(location)
        except Exception:
            mat = scipy.io.loadmat(str(location))
        data = {i: refactor_lumerical_mat(mat[i]) for i in mat}
        db[location.stem] = data

    if delete:
        location.unlink()


def compile_data(
        location: Optional[Union[str, Path]],
        db_location: Optional[Union[str, Path]],
        with_log: bool = False,
        with_tqdm: bool = True,
        use_multiprocessing: bool = True,
        override: bool = False,
        delete: bool = False,
) -> Path:
    location = Path(location).expanduser().absolute()
    db_location = Path(db_location).expanduser().absolute()

    if not location.exists():
        raise ValueError(f"Location {location} does not exist")

    if location.is_file():
        if location.suffix != ".mat":
            raise ValueError(f"Location {location} must be a mat file")

        mat_files = [location]
        sqlite_files = []
    else:
        mat_files = sorted(list(location.glob("*.mat")))
        sqlite_files = sorted(list(location.glob("*.sqlite")))

    if override or not db_location.exists():
        SqliteDeDuplicationDict(db_location, flag="n").close()

    tqdm_prams = dict(ascii=True, position=0, leave=True)
    if with_tqdm:
        mat_files = tqdm(
            mat_files,
            desc=f"Loading {location.name} (mat)",
            total=len(mat_files),
            **tqdm_prams
        )
        sqlite_files = tqdm(
            sqlite_files,
            desc=f"Loading {location.name} (sqlite)",
            total=len(sqlite_files),
            **tqdm_prams
        )

    if use_multiprocessing and len(mat_files) > 1:
        with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
            pool.map(partial(mat_to_db, db_location=db_location, delete=delete), mat_files)
    else:
        for file in mat_files:
            mat_to_db(file, db_location=db_location, delete=delete)

    with SqliteDeDuplicationDict(db_location) as db:
        for i, file in enumerate(sqlite_files):
            with SqliteDeDuplicationDict(file, flag="r") as run_db:
                for key in run_db:
                    if key in db:
                        continue
                    db[key] = run_db[key]
            if with_log:
                print(f"{i + 1}/{len(sqlite_files)}: {file.name}")

    return db_location


def load_data(
        location: Optional[Union[str, Path]] = None,
        **kwargs
) -> SqliteDeDuplicationDict:
    db_location = Path(location).expanduser().absolute()

    if not db_location.exists():
        raise ValueError(f"Location {db_location} does not exist")

    return SqliteDeDuplicationDict(db_location, flag="r", **kwargs)


def _main():
    args = argparse.ArgumentParser(description="Compile data from lumerical mat files")
    args.add_argument("-s", "--script-name", type=str, default=None, help="Name of the script to compile data for")
    args.add_argument("-l", "--location", type=str, default=None, help="Location of the data to compile")
    args.add_argument("-d", "--db-location", type=str, default=None, help="Location of the data to compile")
    args.add_argument("-q", "--quick-location", type=str, default=None, help="Quick access location")
    args.add_argument("-o", "--override", action="store_true", help="Override existing data")
    args.add_argument("-r", "--remove", action="store_true", help="Delete mat files after compilation")
    args.add_argument("-c", "--with-console-log", action="store_true", help="Print log to console")
    args.add_argument("-p", "--no-progress-bar", action="store_false", help="Disable progress bar")
    args.add_argument("-m", "--no-multiprocessing", action="store_false", help="Disable multiprocessing")
    args = args.parse_args()

    if args.script_name is None and args.location is None:
        raise ValueError("Either script_name or location must be specified")

    if args.script_name is not None and args.location is not None:
        raise ValueError("Only one of script_name or location must be specified")

    if args.location is None:
        args.location = get_results_path().joinpath(args.script_name).absolute()
    else:
        args.location = Path(args.location).expanduser().absolute()

    if args.db_location is None:
        args.db_location = args.location.parent.joinpath(f"{args.location.name}.sqlite")
    else:
        args.db_location = Path(args.db_location).expanduser().absolute()

    if args.no_progress_bar and args.with_console_log:
        raise ValueError("Cannot use progress bar with console log")

    using_quick_location = False
    if args.quick_location is not None:
        args.quick_location = Path(args.quick_location).expanduser().absolute()

        if args.quick_location.exists() and args.quick_location.is_dir():
            args.old_db_location = args.db_location
            args.db_location = args.quick_location.joinpath(args.db_location.name)
            using_quick_location = True

    compile_data(
        location=args.location,
        db_location=args.db_location,
        override=args.override,
        delete=args.remove,
        with_log=args.with_console_log,
        with_tqdm=args.no_progress_bar,
        use_multiprocessing=args.no_multiprocessing,
    )

    if using_quick_location:
        shutil.move(args.db_location, args.old_db_location)


if __name__ == '__main__':
    _main()
