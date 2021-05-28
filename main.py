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
    uri, _, _ = start_ns(host=HOST, port=PORT)
    print(f"NS running on {uri.location}")
    print(f"URI = {uri.protocol}:{uri.object}@{uri.location}")
    while True:
        pass


@app.command()
def create_node():
    pool = NodePool(M)
    node_id = pool.get_aviable_identifier()
    other_node = pool.get_random_node()
    node = Node(node_id, pool)
    node.join(other_node)
    node.start_loop()


if __name__ == "__main__":
    app()
