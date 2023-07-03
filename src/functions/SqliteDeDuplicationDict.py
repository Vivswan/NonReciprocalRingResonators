import pickle
import sqlite3
import zlib
from typing import TypeVar, MutableMapping, Iterator

import numpy as np
from deduplicationdict import DeDuplicationDict
from sqlitedict import SqliteDict

KT = TypeVar('KT')  # Key type.
VT = TypeVar('VT')  # Value type.
T_co = TypeVar('T_co', covariant=True)  # Any type covariant containers.
VT_co = TypeVar('VT_co', covariant=True)  # Value type covariant containers.


class SqliteDeDuplicationDict(MutableMapping):
    def __init__(self, *args, **kwargs):
        super().__init__()

        kwargs["autocommit"] = True
        kwargs["outer_stack"] = False
        kwargs["journal_mode"] = "OFF"

        self.value_dict = SqliteDict(*args, **{
            **kwargs,
            "encode": self.encode_value_dict,
            "decode": self.decode_value_dict,
            "tablename": "value_dict",
        })

        kwargs["flag"] = "c" if self.value_dict.flag == "n" else self.value_dict.flag
        self.key_dict = SqliteDict(*args, **{
            **kwargs,
            "encode": self.encode_key_dict,
            "decode": self.decode_key_dict,
            "tablename": "key_dict",
        })

        self.main_dict = DeDuplicationDict()
        self.main_dict.hash_length = 32
        self.main_dict.value_dict = self.value_dict
        self.main_dict.key_dict = self.key_dict

        self.compress_level = 4

    def __setitem__(self, key: KT, value: VT) -> None:
        self.main_dict.__setitem__(key, value)

    def __delitem__(self, key: KT) -> None:
        self.main_dict.__delitem__(key)

    def __getitem__(self, key: KT) -> VT_co:
        return self.main_dict.__getitem__(key)

    def __len__(self) -> int:
        return self.main_dict.__len__()

    def __iter__(self) -> Iterator[T_co]:
        return self.main_dict.__iter__()

    def encode_value_dict(self, obj):
        return sqlite3.Binary(zlib.compress(pickle.dumps(obj, pickle.HIGHEST_PROTOCOL), level=self.compress_level))

    @staticmethod
    def decode_value_dict(obj):
        return pickle.loads(zlib.decompress(bytes(obj)))

    def encode_key_dict(self, obj):
        if isinstance(obj, dict):
            raise ValueError("dict not allowed")
        if isinstance(obj, DeDuplicationDict):
            obj = obj._get_key_dict()
        if isinstance(obj, np.ndarray):
            obj = obj.tolist()
        return sqlite3.Binary(zlib.compress(pickle.dumps(obj, pickle.HIGHEST_PROTOCOL), level=self.compress_level))

    def decode_key_dict(self, obj):
        obj = pickle.loads(zlib.decompress(bytes(obj)))
        if isinstance(obj, dict):
            obj = DeDuplicationDict().from_json_save_dict({
                "key_dict": obj,
                "value_dict": self.value_dict,
            })
        return obj

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def __str__(self):
        return f"SqliteDeDuplicationDict({self.main_dict})"

    def __repr__(self):
        return f"SqliteDeDuplicationDict({self.main_dict})"

    def __bool__(self):
        return bool(self.main_dict)

    def close(self, do_log=True, force=False):
        self.key_dict.close(do_log=do_log, force=force)
        self.value_dict.close(do_log=do_log, force=force)

    def terminate(self):
        self.key_dict.terminate()
        self.value_dict.terminate()

    def __del__(self):
        self.close()
