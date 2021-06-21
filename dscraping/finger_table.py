import dataclasses
from typing import Iterable, List, Optional


@dataclasses.dataclass
class FingerData:
    start: int
    node: Optional[int]


class FingerTable:
    def __init__(self, node_id: int, size: int) -> None:
        self.node_id: int = node_id
        self.size: int = size

        # FingerTable[0].node is the predecessor node in the chord cycle
        self.ft: List[FingerData] = [FingerData(node_id, node_id)] + [
            FingerData(self.start_index(i), node_id) for i in range(1, size + 1)
        ]

    def start_index(self, i: int) -> int:
        return (self.node_id + 2 ** (i - 1)) % 2 ** self.size

    def __getitem__(self, key: int) -> FingerData:
        return self.ft[key]

    def __setitem__(self, key: int, node: Optional[int]) -> None:
        self.ft[key].node = node

    def __iter__(self) -> Iterable[FingerData]:
        yield from self.ft

    def __str__(self) -> str:
        return f"Finger Table of {self.node_id}\n" + "\n".join(self.ft)
