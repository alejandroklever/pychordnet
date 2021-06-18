from Pyro5.nameserver import start_ns
import typer
from chord import Linker, ChordNode


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
def create_node(id: int = -1):
    pool = Linker(M)

    node_id = pool.get_aviable_chord_identifier() if id == -1 else id % 2 ** M
    print(f"Node id => {node_id}")
    other_node = pool.get_random_node()
    if other_node is not None:
        print(f"Join node => {other_node.id}")

    node = ChordNode(node_id, pool)
    uri = pool.register_node(node)

    print(f"Uri => {uri}")
    node.join(other_node)

    if other_node is None:
        print(f"Created node {node_id}")
    else:
        print(f"Created node {node_id} joined to node {other_node.id}")
    node.start_loop()


if __name__ == "__main__":
    # app()
    create_node(6)
