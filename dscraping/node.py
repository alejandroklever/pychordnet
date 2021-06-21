from Pyro5.errors import PyroError
from dscraping.monitoring import echo_error
from enum import Enum, auto
import random
from typing import Any, Set
from Pyro5.api import Daemon, locate_ns, Proxy
from Pyro5.nameserver import NameServer, NameServerDaemon


class NodeType(Enum):
    none = auto()
    chord = auto()
    router = auto()
    client = auto()


class Node:
    _id: int
    _node_type: NodeType


class Linker:
    """
    This class is an api to comunicate any member of the network with the resource server
    """

    def __init__(self, m: int) -> None:
        self.BITS_COUNT = m
        self.MAX = 2 ** m
        self.name_server = locate_ns()
        self.daemon = Daemon()
        self.total_nodes = set(range(self.MAX))

    def register_node(self, node: "Node"):
        object_id = f"node.{node._node_type.name}.{node._id}"
        uri = self.daemon.register(node, object_id)
        self.name_server.register(
            object_id, uri, metadata=[f"node.{node._node_type.name}"]
        )
        return uri

    def remove_node(self, node_type: "NodeType", node_id: int):
        try:
            self.name_server.remove(f"node.{node_type.name}.{node_id}")
        except PyroError:
            # In case that name server Proxy is not owned by this thread
            ns = locate_ns()
            ns.remove(f"node.{node_type.name}.{node_id}")
        self.daemon.shutdown()

    def get_node(self, node_type: "NodeType", i: int) -> Proxy:
        return Proxy(self.node_uri(node_type, i))

    def get_nodes(self, node_type: "NodeType") -> Set[int]:
        try:
            nodes = self.name_server.yplookup(meta_all=[f"node.{node_type.name}"])
        except PyroError:
            # In case that name server Proxy is not owned by this thread
            ns = locate_ns()
            nodes = ns.yplookup(meta_all=[f"node.{node_type.name}"])

        return set(
            int(node_name.replace(f"node.{node_type.name}.", "")) for node_name in nodes
        )

    def get_aviable_chord_identifier(self) -> int:
        alive_nodes = self.get_nodes(NodeType.chord)
        aviables_nodes = list(self.total_nodes - alive_nodes)
        return random.choice(aviables_nodes)

    def get_random_node(self, node_type: "NodeType") -> Any:
        nodes = self.get_nodes(node_type)
        if not nodes:
            return None
        return self.get_node(node_type, random.choice(list(nodes)))

    def exists_node(self, node_type: "NodeType", id: int) -> bool:
        return id in self.get_nodes(node_type)

    def start_loop(self):
        self.daemon.requestLoop()

    @staticmethod
    def node_uri(node_type: "NodeType", i: int) -> str:
        return f"PYRONAME:node.{node_type.name}.{i}"
