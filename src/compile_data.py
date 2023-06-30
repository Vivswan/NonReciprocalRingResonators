from __future__ import annotations

import argparse
import multiprocessing
from functools import partial
from pathlib import Path
from typing import Union, Optional

import mat73
import numpy as np
import scipy
from tqdm import tqdm

from src.functions.SqliteDeDuplicationDict import SqliteDeDuplicationDict
from z_outputs.results import get_results_path


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
    location = Path(location).absolute()
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
        db_location: Optional[Union[str, Path]] = None,
        with_tqdm: bool = True,
        use_multiprocessing: bool = True,
        override: bool = False,
        delete: bool = False,
) -> Path:
    location = Path(location).absolute()

    if not location.exists():
        raise ValueError(f"Location {location} does not exist")

    if db_location is None:
        db_location = location.parent.joinpath(f"{location.name}.sqlite")
    else:
        db_location = Path(db_location).absolute()

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
        for file in sqlite_files:
            with SqliteDeDuplicationDict(file, flag="r") as run_db:
                for key in run_db:
                    if key in db:
                        continue
                    db[key] = run_db[key]

    return db_location


def load_data(
        script_name: Optional[str] = None,
        location: Optional[Union[str, Path]] = None,
        force=False,
        **kwargs
) -> SqliteDeDuplicationDict:
    if location is None and script_name is None:
        raise ValueError("Either script_name or location must be specified")

    if location is None:
        db_location = get_results_path().joinpath(f"{script_name}.sqlite").absolute()
    else:
        location = Path(location)
        db_location = location.parent.joinpath(f"{location.name}.sqlite").absolute()

    if not db_location.exists() or force:
        db_location = compile_data(location, db_location=db_location, **kwargs)

    return SqliteDeDuplicationDict(db_location, flag="r", **kwargs)


def _main():
    args = argparse.ArgumentParser(description="Compile data from lumerical mat files")
    args.add_argument("-s", "--script_name", type=str, default=None, help="Name of the script to compile data for")
    args.add_argument("-l", "--location", type=str, default=None, help="Location of the data to compile")
    args.add_argument("-d", "--db_location", type=str, default=None, help="Location of the data to compile")
    args.add_argument("-o", "--override", action="store_true", help="Override existing data")
    args.add_argument("-r", "--remove", action="store_true", help="Delete mat files after compilation")
    args.add_argument("-p", "--no_progress_bar", action="store_false", help="Disable progress bar")
    args.add_argument("-m", "--no_multiprocessing", action="store_false", help="Disable multiprocessing")
    args = args.parse_args()

    if args.script_name is None and args.location is None:
        raise ValueError("Either script_name or location must be specified")

    if args.script_name is not None and args.location is not None:
        raise ValueError("Only one of script_name or location must be specified")

    if args.location is None:
        args.location = get_results_path().joinpath(args.script_name).absolute()

    compile_data(
        location=args.location,
        db_location=args.db_location,
        override=args.override,
        delete=args.remove,
        with_tqdm=args.no_progress_bar,
        use_multiprocessing=args.no_multiprocessing,
    )


if __name__ == '__main__':
    _main()
