import hashlib
import random
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Union

from Pyro5.api import Daemon, Proxy, expose, locate_ns
from Pyro5.errors import CommunicationError

from .node import Node, NodeType, Linker
from .finger_table import FingerTable
from .hash_table import HashTable
from .monitoring import echo_error, monitor

USE_MONITOR = False


@expose
class ChordNode(Node):

    _node_type = NodeType.chord

    def __init__(
        self,
        id: int,
        linker: Linker,
        cache_size: int,
        use_stabilization: bool = True,
        stabilization_interval: int = 1000,
        fix_finger_interval: int = 1000,
    ) -> None:
        self._id = id
        self.linker = linker
        self._ft = FingerTable(id, linker.BITS_COUNT)
        self.MAX = linker.MAX
        self.BIT_COUNT = linker.BITS_COUNT

        self.use_stabilization = use_stabilization
        self.stabilization_interval = stabilization_interval
        self.fixing_fingers_interval = fix_finger_interval

        self.hash_table = HashTable(cache_size)
        self.executor = ThreadPoolExecutor()

    @property
    def id(self) -> int:
        return self._id

    @property
    def finger_table(self) -> FingerTable:
        return self._ft

    @property
    def node_type(self) -> NodeType:
        return self._node_type

    @property
    def serialized_finger_table(self) -> List[str]:
        return [str(x) for x in self.finger_table]

    @property
    def serialized_hash_table_keys(self):
        return [s for s in self.hash_table]

    ###################################
    # Successor - Predecessor Section #
    ###################################
    @property
    def successor(self) -> Proxy:
        """Return the Proxy objecto to the successor node"""
        return self.linker.get_node(self.node_type, self._ft[1].node)

    @property
    def predecessor(self) -> Proxy:
        """Return the Proxy objecto to the predecessor node"""
        return self.linker.get_node(self.node_type, self._ft[0].node)

    @property
    def successor_id(self) -> Optional[int]:
        return self._ft[1].node

    @property
    def predecessor_id(self) -> Optional[int]:
        return self._ft[0].node

    def set_successor(self, value: Optional[int]):
        self._ft[1].node = value

    def set_predecessor(self, value: Optional[int]):
        self._ft[0].node = value

    #######
    # End #
    #######

    #########
    # Utils #
    #########
    def hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode()).hexdigest(), base=16) % self.MAX

    def in_between(self, k: int, a: int, b: int, equals: bool = True) -> bool:
        a %= self.MAX
        b %= self.MAX

        if a == b:
            return equals
        if a < b:
            return a <= k < b
        return a <= k < b + self.MAX or (a <= k + self.MAX and k < b)

    #######
    # End #
    #######

    ##################
    # Hash Table API #
    ##################
    @monitor(active=USE_MONITOR)
    def insert(self, key: str, value: str):
        hashed_key = self.hash(key)
        node = self.find_successor(hashed_key)
        if node.id == self.id:
            self.hash_table[key] = value
        else:
            node.insert(key, value)

    @monitor(active=USE_MONITOR)
    def constains(self, key: str) -> bool:
        hashed_key = self.hash(key)
        node = self.find_successor(hashed_key)
        return (node.id == self.id and key in self.hash_table) or (
            node.id != self.id and node.contains(key)
        )

    @monitor(active=USE_MONITOR)
    def get(self, key: str) -> Optional[str]:
        hashed_key = self.hash(key)
        node = self.find_successor(hashed_key)
        if node.id == self.id:
            return self.hash_table[key] if key in self.hash_table else None
        else:
            return node.get(key)

    @monitor(active=USE_MONITOR)
    def pop_in_interval(self, start: int, end: int) -> Dict[str, str]:
        """
        Pop keys of the cache hashed in interval [start, end]
        """

        data = {
            x: self.hash_table[x]
            for x in self.hash_table
            if self.in_between(self.hash(x), start, end + 1)
        }
        self.hash_table.pop_many(data.keys())
        return data

    @monitor(active=USE_MONITOR)
    def update_hash_table(self):
        """
        Update the node cache transfering the keys from it successor
        The keys of a node are hashed in interval [predecessor + 1, self.id]
        """
        if self.successor_id == self.id:
            return

        data = self.successor.pop_in_interval(self.predecessor_id + 1, self.id)
        self.hash_table.update(data)

    @monitor(active=USE_MONITOR)
    def update_hash_table_with_keys(self, keys):
        self.hash_table.update(keys)

    #######
    # End #
    #######

    ##########################
    # Find Successor Section #
    ##########################
    @monitor(active=USE_MONITOR)
    def find_successor(self, k: int) -> Union["ChordNode", Proxy]:
        node = self.find_predecessor(k)
        return node.successor

    @monitor(active=USE_MONITOR)
    def find_predecessor(self, key: int) -> Union["ChordNode", Proxy]:
        node = self

        while not self.in_between(key, node.id + 1, node.successor_id + 1):
            node = node.closest_preceding_finger(key)

        return node

    @monitor(active=USE_MONITOR)
    def closest_preceding_finger(self, key: int) -> Union["ChordNode", Proxy]:
        ft = self.finger_table

        for i in range(self.linker.BITS_COUNT, 0, -1):
            if ft[i].node is not None and self.in_between(ft[i].node, self.id + 1, key):
                node = self.linker.get_node(self.node_type, self._ft[i].node)
                return node
        return self

    #######
    # End #
    #######

    @monitor(active=USE_MONITOR)
    def join(self, anchor_node):
        if not self.use_stabilization and anchor_node is not None:
            self.init_finger_table(anchor_node)
            self.update_others()
            self.update_hash_table()
        elif self.use_stabilization:
            if anchor_node is not None:
                for entry in self.finger_table:
                    entry.node = None

                self.set_successor(anchor_node.find_successor(self.id).id)

            self.executor.submit(self.stabilize_subprocess)
            self.executor.submit(self.fix_fingers_subprocess)

    ##############################
    # Join without stabilization #
    ##############################
    @monitor(active=USE_MONITOR)
    def init_finger_table(self, anchor_node: Union["ChordNode", Proxy]):
        ft = self.finger_table  # I do this so as not to write a lot

        successor = anchor_node.find_successor(ft[1].start)
        ft[1].node = successor.id
        ft[0].node = successor.predecessor_id
        successor.set_predecessor(self.id)

        for i in range(1, self.linker.BITS_COUNT):
            if self.in_between(ft[i + 1].start, self.id, ft[i].node):
                ft[i + 1].node = ft[i].node
            else:
                succ = anchor_node.find_successor(ft[i + 1].start).id
                if self.in_between(self.id, ft[i + 1].start, succ, False):
                    ft[i + 1] = self.id
                else:
                    ft[i + 1] = succ

    @monitor(active=USE_MONITOR)
    def update_others(self):
        for i in range(1, self.linker.BITS_COUNT + 1):
            node = self.find_predecessor((self.id - 2 ** (i - 1)) % self.MAX)
            node.update_finger_table(self.id, i)

    @monitor(active=USE_MONITOR)
    def update_finger_table(self, new_id: int, index: int):
        ft = self.finger_table

        if self.in_between(new_id, self.id, ft[index].node):
            ft[index].node = new_id

            # node with the "new_id" id is calling remote this node
            # and it finger table is computed correctly
            if self.predecessor_id == new_id:
                return
            predecessor = self.predecessor
            predecessor.update_finger_table(new_id, index)

    #######
    # End #
    #######

    ###########################
    # Join with stabilization #
    ###########################
    @monitor(active=USE_MONITOR)
    def stabilize_subprocess(self):
        interval = self.stabilization_interval
        interval_over_4 = interval // 4
        while True:
            waiting_time = random.randint(
                interval - interval_over_4, interval + interval_over_4
            )  # milliseconds

            try:
                self.stabilize()
            except Exception as e:
                echo_error(e)

            time.sleep(waiting_time / 1000)

    @monitor(active=USE_MONITOR)
    def stabilize(self):
        node_id = self.successor.predecessor_id

        # check if exists a better succesor
        # print(f"\t{node_id} in ({self.id}, {self.successor_id})")
        if node_id is not None and self.in_between(
            node_id, self.id + 1, self.successor_id
        ):
            self.set_successor(node_id)

        self.successor.notify(self)
        self.update_hash_table()

    @monitor(active=USE_MONITOR)
    def notify(self, node):
        # check if node has not been eliminated from the network
        if self.predecessor_id is not None and self.predecessor_id != node.id:
            try:
                self.predecessor.id
            except CommunicationError:
                self.set_predecessor(None)

        # check if exist a better predecessor
        if self.predecessor_id is None or self.in_between(
            node.id, self.predecessor_id + 1, self.id
        ):
            self.set_predecessor(node.id)
            self.predecessor.update_hash_table()

    @monitor(active=USE_MONITOR)
    def fix_fingers_subprocess(self):
        interval = self.stabilization_interval
        interval_over_4 = interval // 4
        while True:
            waiting_time = random.randint(
                interval - interval_over_4, interval + interval_over_4
            )  # milliseconds
            try:
                self.fix_fingers()
            except Exception as e:
                echo_error(e)

            time.sleep(waiting_time / 1000)

    @monitor(active=USE_MONITOR)
    def fix_fingers(self):
        if self.BIT_COUNT < 2:
            return
        i = random.randint(2, self.BIT_COUNT)
        self.finger_table[i].node = self.find_successor(self.finger_table[i].start).id

    #######
    # End #
    #######

    #############
    # disconect #
    #############
    @monitor(active=USE_MONITOR)
    def disconnect(self):
        succ = self.successor
        pred = self.predecessor
        succ.set_predecessor(pred.id)
        pred.set_successor(succ.id)
        succ.update_hash_table_with_keys(
            {key: self.hash_table[key] for key in self.hash_table}
        )

        succ._pyroRelease()
        pred._pyroRelease()
        self.linker.remove_node(self.node_type, self.id)

    #######
    # End #
    #######

    def start_loop(self):
        self.linker.start_loop()

    def __str__(self) -> str:
        return f"Node.{self.id}"

    def __repr__(self) -> str:
        return str(self)
