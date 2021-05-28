from typing import Any, List, Set

import Pyro5
import Pyro5.api
import dataclasses

from Pyro5.nameserver import NameServer


@dataclasses.dataclass
class FingerData:
    start: int
    node: int


class FingerTable:
    def __init__(self, node_id: int, size: int) -> None:
        self.node_id: int = node_id
        self.size: int = size
        self.ft: List[int] = [FingerData(node_id - 1, node_id)] + [
            FingerData(self.map(i), node_id) for i in range(1, size + 1)
        ]

    def __getitem__(self, item: int) -> FingerData:
        return self.ft[item]

    def __setitem__(self, key: int, item: int) -> None:
        self.ft[key] = item

    def map(self, i: int) -> int:
        return (self.node_id + 2 ** (i - 1)) % 2 ** self.size


class NodePool:
    def __init__(self, m: int) -> None:
        self.BITS_COUNT = m
        self.MAX = 2 ** m
        self.name_server = Pyro5.api.locate_ns()
        self.deamon = Pyro5.api.Daemon()
        self.total_nodes = set(range(self.MAX))

    def register_node(self, node):
        object_id = f"node.{id}"
        uri = self.deamon.register(node, object_id)
        self.name_server.register(object_id, uri, metadata=["node"])

    def get_node(self, i: int) -> Any:
        return Pyro5.api.Proxy(self.node_uri(i))  

    def get_nodes(self) -> Set[int]:
        nodes = self.name_server.yplookup(meta_all=["node"])
        return set(int(node_name.replace("node.", "")) for node_name in nodes)

    def get_aviable_identifier(self) -> int:
        alive_nodes = self.get_nodes()
        aviables_nodes = self.get_nodes - alive_nodes
        return aviables_nodes.pop()
    
    def get_random_node(self) -> Any:
        nodes = self.get_nodes()
        if not nodes:
            return None
        return self.get_node(nodes.pop())

    def start_loop(self):
        self.deamon.requestLoop()

    @staticmethod
    def node_uri(i: int) -> str:
        return f"PYRONAME:node.{i}"


@Pyro5.api.expose
class Node:
    def __init__(self, id: int, pool: NodePool) -> None:
        self.id = id
        self.pool = pool
        self.ft = FingerTable(id, pool.BITS_COUNT)

    @property
    def identifier(self):
        return self.id

    @property
    def successor(self):
        successor = self.pool.get_node(self.ft[1].node)
        return successor

    def set_successor(self, value):
        self.ft[1].node = value

    @property
    def successor_id(self):
        return self.ft[1].node

    @property
    def predecessor(self):
        return self.pool.get_node(self.ft[0].node)

    @property
    def predecessor_id(self):
        return self.ft[0].node

    def set_predecessor(self, value: int):
        self.ft[0].node = value

    def find_succesor(self, k: int):
        node = self.find_predecessor(k)
        return node.successor

    def find_predecessor(self, k: int):
        node = self
        while not (node.id < k <= node.successor_id):
            node = node.closest_preceding_finger(k)
        return node

    def closest_preceding_finger(self, k: int):
        for i in range(self.pool.BITS_COUNT, 0, -1):
            if self.id < self.ft[i].node < k:
                node = self.pool.get_node(i)
                return node
        return self

    def join(self, other_node):
        if other_node is not None:
            self.init_finger_table(other_node)
            self.update_others()
        

    def init_finger_table(self, other_node):
        successor = self.successor

        self.set_successor(other_node.find_succesor(self.ft[1].start).identifier)

        self.set_predecessor(self.successor_id - 1)
        successor.set_predecessor(self.id)

        for i in range(1, self.pool.BITS_COUNT):
            if self.id <= self.ft[i + 1].start <= self.ft[i].node:
                self.ft[i + 1].node = self.ft[i].node
            else:
                self.ft[i + 1].node = other_node.find_succesor(
                    self.ft[1].start
                ).identifier

    def update_others(self):
        for i in range(1, self.pool.BITS_COUNT + 1):
            node = self.find_predecessor(self.id - 2 ** (i - 1))
            node.update_finger_table(self.id, i)

    def update_finger_table(self, s, i):
        if self.id <= s < self.ft[i].node:
            self.ft[i].node = s
            predecessor = self.predecessor
            predecessor.update_finger_table(s, i)

    def start_loop(self):
        self.pool.start_loop()
