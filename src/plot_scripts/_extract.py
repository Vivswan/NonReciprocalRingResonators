import numpy as np
from tqdm import tqdm

from src.compile_data import SqliteDeDuplicationDict


def extract(data: SqliteDeDuplicationDict, *args):
    results = []

    for v in tqdm(data.values(), ascii=True, desc=f"Extracting {'|'.join(args)}"):
        for arg in args:
            v = v[arg]

        results.append(v)
    return np.array(results)
