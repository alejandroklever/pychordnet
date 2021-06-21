from typing import Dict, Iterable, Union
from collections import OrderedDict


class HashTable:
    def __init__(self, max_size: int) -> None:
        self.dict: OrderedDict[str, str] = OrderedDict()
        self.__max_size: int = max_size

    def update(self, other: Union["HashTable", Dict[str, str]]):
        if isinstance(other, (HashTable, dict, OrderedDict)):
            for key in other:
                self[key] = other[key]

    def pop(self, key: str):
        del self.dict[key]

    def pop_many(self, keys: Iterable[str]):
        for k in keys:
            self.pop(k)

    def __getitem__(self, key: str) -> str:
        return self.dict[key]

    def __setitem__(self, key, value):
        if len(self.dict) == self.__max_size:
            self.dict.popitem(last=False)
        self.dict[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.dict

    def __iter__(self):
        yield from self.dict
