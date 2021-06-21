import time
from multiprocessing import Process

import Pyro5.api
import requests

from .node import Linker, Node, NodeType

MAX_BUFFER = 4


@Pyro5.api.expose
class RouterNode(Node):
    _node_type = NodeType.router

    def __init__(self, linker: Linker) -> None:
        self._buffer = []
        self._full = False
        self.linker = linker
        self._id = self._find_id()

    @property
    def buffer(self):
        return self._buffer

    @property
    def full(self):
        return self._full

    @property
    def id(self):
        return self._id

    def set_full(self, value):
        self._full = value

    def add_to_buffer(self, value):
        self._buffer.append(value)

    def _find_id(self) -> int:
        alive_nodes = self.linker.get_nodes(NodeType.router)
        max_id = max(alive_nodes) if alive_nodes else 0
        return max_id + 1

    def register_url(self, url, client_id):
        self.add_to_buffer((url, client_id))
        self.set_full(len(self.buffer) == MAX_BUFFER)

    def request_scrapping(self, url, client_id):
        if self.full:
            # the request cannot be taken, node is busy
            return (1, None)
        self.register_url(url, client_id)
        # the request has been buffered
        return (0, url)

    def send_response(self, response, client_id):
        client = self.linker.get_node(NodeType.client, client_id)
        client.set_response([response])

    def main_loop(self):
        try:
            while True:
                if self.buffer == []:
                    time.sleep(1)
                    continue
                url, client_id = self.buffer.pop()
                self.set_full(len(self.buffer) == MAX_BUFFER)
                print(f"Procesing request from client {client_id}")
                response = requests.get(url)
                self.send_response(response, client_id)
        except KeyboardInterrupt:
            return

    def scrap(self, url):
        return requests.get(url).text

    def start_loop(self):
        p = Process(target=self.main_loop)
        p.start()
        self.linker.start_loop()
        p.join()
        self.linker.remove_node(self._node_type, self.id)
