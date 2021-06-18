import dataclasses
import inspect
import random
import time
from typing import Any, Iterable, List, Set

import Pyro5
import Pyro5.api
import typer

USE_MONITOR = True


def echo(message: str):
    typer.echo(typer.style(message, fg=typer.colors.GREEN))


def echo_error(message: str):
    typer.echo(typer.style(message, fg=typer.colors.RED, bold=True))


def echo_warning(message: str):
    typer.echo(typer.style(message, fg=typer.colors.YELLOW, bold=True))


def monitor(active: bool = True):
    def decorator(func):
        def wrapper(*args):
            args_names = inspect.getfullargspec(func)[0][1:]
            args_values = args[1:]
            args_str = ", ".join(
                f"{name}={value}" for name, value in zip(args_names, args_values)
            )
            s = f"{args[0]} call => {func.__name__} ({args_str})"
            echo(s)
            try:
                result = func(*args)
            except Exception as e:
                raise e
            return result

        return wrapper if active else func

    return decorator


@dataclasses.dataclass
class FingerData:
    start: int
    node: int


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

    def __getitem__(self, item: int) -> FingerData:
        return self.ft[item]

    def __setitem__(self, key: int, node: int) -> None:
        self.ft[key].node = node

    def __iter__(self) -> Iterable[FingerData]:
        return iter(self.ft)

    def __str__(self) -> str:
        return f"Finger Table of {self.node_id}\n" + "\n".join(self.ft)


class NodePool:
    def __init__(self, m: int) -> None:
        self.BITS_COUNT = m
        self.MAX = 2 ** m
        self.name_server = Pyro5.api.locate_ns()
        self.deamon = Pyro5.api.Daemon()
        self.total_nodes = set(range(self.MAX))

    def register_node(self, node):
        object_id = f"node.{node.id}"
        uri = self.deamon.register(node, object_id)
        self.name_server.register(object_id, uri, metadata=["node"])
        return uri

    def get_node(self, i: int) -> Any:
        return Pyro5.api.Proxy(self.node_uri(i))

    def get_nodes(self) -> Set[int]:
        nodes = self.name_server.yplookup(meta_all=["node"])
        return set(int(node_name.replace("node.", "")) for node_name in nodes)

    def get_aviable_identifier(self) -> int:
        alive_nodes = self.get_nodes()
        aviables_nodes = list(self.total_nodes - alive_nodes)
        return random.choice(aviables_nodes)

    def get_random_node(self) -> Any:
        nodes = self.get_nodes()
        if not nodes:
            return None
        return self.get_node(random.choice(list(nodes)))

    def start_loop(self):
        self.deamon.requestLoop()

    @staticmethod
    def node_uri(i: int) -> str:
        return f"PYRONAME:node.{i}"


@Pyro5.api.expose
class Node:
    def __init__(self, id: int, pool: NodePool) -> None:
        self._id = id
        self.pool = pool
        self.MAX = pool.MAX
        self.BIT_COUNT = pool.BITS_COUNT
        self.ft = FingerTable(id, pool.BITS_COUNT)

    @property
    def id(self):
        return self._id

    @property
    def successor(self):
        successor = self.pool.get_node(self.ft[1].node)
        return successor

    @property
    def successor_id(self) -> int:
        return self.ft[1].node

    def set_successor(self, value):
        self.ft[1].node = value

    @property
    def predecessor(self):
        return self.pool.get_node(self.ft[0].node)

    @property
    def predecessor_id(self):
        return self.ft[0].node

    def set_predecessor(self, value: int):
        self.ft[0].node = value

    def in_between(self, k: int, a: int, b: int, equals: bool = True) -> bool:
        a %= self.MAX
        b %= self.MAX

        if a == b:
            return equals
        if a < b:
            return a <= k < b
        return a <= k < b + self.MAX or (a <= k + self.MAX and k < b)

    @monitor(active=USE_MONITOR)
    def find_successor(self, k: int):
        node = self.find_predecessor(k)
        return node.successor

    @monitor(active=USE_MONITOR)
    def find_predecessor(self, key: int):
        node = self

        while not self.in_between(key, node.id + 1, node.successor_id + 1):
            # print(f"\t{key} not in ({node.id}, {self.successor_id}]")
            # time.sleep(1)
            node = node.closest_preceding_finger(key)

        return node

    @monitor(active=USE_MONITOR)
    def closest_preceding_finger(self, key: int):
        ft = self.ft

        self.print_finger_table(tab_depth=1)
        for i in range(self.pool.BITS_COUNT, 0, -1):
            if self.in_between(ft[i].node, self.id + 1, key):
                # print(f"\t{ft[i].node} in ({self.id}, {key})")
                # time.sleep(1)
                node = self.pool.get_node(self.ft[i].node)
                return node
        return self

    @monitor(active=USE_MONITOR)
    def join(self, anchor_node):
        if anchor_node is not None:
            self.init_finger_table(anchor_node)
            self.update_others()

    @monitor(active=USE_MONITOR)
    def init_finger_table(self, anchor_node: "Node"):
        ft = self.ft  # I do this so as not to write a lot

        ft[1].node = anchor_node.find_successor(ft[1].start).id
        ft[0].node = self.successor.predecessor_id
        self.successor.set_predecessor(self.id)

        # self.print_finger_table()
        # print()
        for i in range(1, self.pool.BITS_COUNT):
            if self.in_between(ft[i + 1].start, self.id, ft[i].node):
                ft[i + 1].node = ft[i].node
            else:
                succ = anchor_node.find_successor(ft[i + 1].start).id
                if self.in_between(self.id, ft[i + 1].start, succ, False):
                    ft[i + 1] = self.id
                else:
                    ft[i + 1] = succ

            # self.print_finger_table()
            # print()

    @monitor(active=USE_MONITOR)
    def update_others(self):
        for i in range(1, self.pool.BITS_COUNT + 1):
            # print(f"for i = {i}")
            node = self.find_predecessor((self.id - 2 ** (i - 1)) % self.MAX)
            node.update_finger_table(self.id, i)

    @monitor(active=USE_MONITOR)
    def update_finger_table(self, new_id: int, index: int):
        ft = self.ft

        if self.in_between(new_id, self.id, ft[index].node):
            print(f"\t{new_id} in ({self.id}, {ft[index].node})")
            ft[index].node = new_id

            # self.print_finger_table()

            # node with the "new_id" id is calling remote this node
            # and it finger table is computed correctly
            if self.predecessor_id == new_id:
                return
            predecessor = self.predecessor
            predecessor.update_finger_table(new_id, index)

    def start_loop(self):
        self.pool.start_loop()

    def print_finger_table(self, tab_depth: int = 0, print_predecessor: bool = True):
        ft = self.ft if print_predecessor else self.ft[1:]
        print("\t" * tab_depth + "Finger Table:")
        for x in ft:
            print(("\t" * (tab_depth + 1)) + f"{x}")

    def __str__(self) -> str:
        return f"Node.{self.id}"

    def __repr__(self) -> str:
        return str(self)
