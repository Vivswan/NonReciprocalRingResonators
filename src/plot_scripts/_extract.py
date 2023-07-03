import numpy as np
from tqdm import tqdm

from src.compile_data import SqliteDeDuplicationDict


def extract(data: SqliteDeDuplicationDict, *args):
    results = []

    for v in tqdm(data.values(), ascii=True, desc=f"Extracting {'|'.join(args)}"):
        try:
            for arg in args:
                v = v[arg]
            results.append(v)
        except KeyError as e:
            print(e)
            results.append(np.nan)
    try:
        results = np.array(results)
    except ValueError:
        pass
    return results
