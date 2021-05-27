from typing import List



class FingerTable:
    def __init__(self, node: 'Node', size: int) -> None:
        self.node = node
        self.size = size
        self.ft: List[int] = [(node.id + 2 ** i) % 2 ** size for i in range(size)]
        self.addresses: List[str] = ['' for _ in range(size)]
        self.ports: List[int] = [0 for _ in range(size)]

    def __getitem__(self, item: int) -> int:
        return self.ft[item]


class Node:
    def __init__(self, id: int, size: int = 5) -> None:
        self.id = id
        self.finger_table = FingerTable(self, 5)

    @property
    def successor(self) -> 'Node':
        return Node(self.finger_table[0], self.finger_table.size)
    
    def find_succesor(self, k: int) -> 'Node':
        node = self.find_predecessor(k)
        return node.successor
    
    def find_predecessor(self, k: int) -> 'Node':
        n = self
        while not n.id < k <= n.successor.id:
            n = n.closest_preceding_finger(k)
        return n
    
    def closest_preceding_finger(self, k: int) -> 'Node':
        for i in range(self.finger_table.size - 1, -1, -1):
            if self.id < self.finger_table[i] < k:
                return Node(self.finger_table[i], self.finger_table.size)
        
        return Node(self.id, self.finger_table.size)
    



if __name__ == "__main__":    
    import Pyro5
    print(Pyro5.config.dump())
