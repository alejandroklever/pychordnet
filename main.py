from Pyro5.nameserver import start_ns
import typer
import Pyro5.api
from chord import NodePool, Node


app = typer.Typer()

M = 3
HOST = "localhost"
PORT = 9090


@app.command()
def start_name_service():
    uri, deamon, _ = start_ns(host=HOST, port=PORT)
    print(f"NS running on {uri.location}")
    print(f"URI = {uri.protocol}:{uri.object}@{uri.location}")
    deamon.requestLoop()


@app.command()
def create_node():
    pool = NodePool(M)

    node_id = pool.get_aviable_identifier()
    other_node = pool.get_random_node()

    node = Node(node_id, pool)
    uri = pool.register_node(node)
    node.join(other_node)

    if other_node is None:
        print(f"Created node {node_id}")
    else:
        print(f"Created node {node_id} joined to node {other_node.id}")
    
    print(f"URI => {uri}")
    node.start_loop()


if __name__ == "__main__":
    app()
