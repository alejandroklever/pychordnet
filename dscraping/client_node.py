import time
from multiprocessing import Process
from typing import List, Optional

from Pyro5.api import expose

from .node import Linker, Node, NodeType


@expose
class ClientNode(Node):
    _node_type = NodeType.client

    def __init__(self, linker: Linker, lines: List) -> None:
        self.linker = linker
        self._id = self._find_id()
        self._response = []
        self.lines = lines

    @property
    def id(self):
        return self._id

    @property
    def node_type(self):
        return self._id

    @property
    def response(self):
        return self._response

    def set_response(self, value):
        self._response = value

    def _find_id(self) -> int:
        alive_nodes = self.linker.get_nodes(NodeType.client)
        max_id = max(alive_nodes) if alive_nodes else 0
        return max_id + 1

    def find_router_node(self):
        return self.linker.get_random_node(NodeType.router)

    def wait_response(self):
        timeout = 0
        while not self.response:
            time.sleep(1)
            timeout += 1
            if timeout == 60:
                return None
        return 0

    def search_data(self, url: str) -> Optional[str]:
        node = self.linker.get_random_node(NodeType.chord)
        value = node.get(url)
        if value is not None:
            return 0, value
        return 1, None

    def insert_data(self, url: str, data: str):
        node = self.linker.get_random_node(NodeType.chord)
        node.insert(url, data)

    def main_loop(self):
        try:
            responses = []
            processed_urls = []
            while len(processed_urls) != len(self.lines):
                for url in self.lines:
                    if url in processed_urls:
                        continue
                    op_code, saved_data = self.search_data(url)
                    if op_code == 1:
                        router_node = self.find_router_node()
                        if router_node is None:
                            print(
                                "The system is busy or unavailable, wait a few seconds and retry"
                            )
                            # give time to the system to recover
                            time.sleep(2)
                            continue
                        print(f"Url requested to node: {router_node.id} - {url}")
                        print("Waiting for response...")
                        response = router_node.scrap(url)
                        print(f"Recived response from node {router_node.id}")
                        self.insert_data(url, response)
                    else:
                        response = saved_data
                    responses.append(response)
                    processed_urls.append(url)
            file = open(f"output.client.{self.id}.txt", "w+")
            file.writelines(list(map(lambda x: str(x), zip(processed_urls, responses))))
            print("Done")
        except KeyboardInterrupt:
            return

    def start_loop(self):
        p = Process(target=self.main_loop)
        p.start()
        self.linker.start_loop()
        p.join()
        self.linker.remove_node(self._node_type, self.id)
