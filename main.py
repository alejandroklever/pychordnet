from Pyro5.nameserver import start_ns
import typer
from dscraping.chord import Linker, ChordNode, NodeType
from dscraping.monitoring import echo


app = typer.Typer()

M = 3
CACHE_SIZE = 5
HOST = "localhost"
PORT = 9090


def echo_finger_table(node_id: int, linker: Linker):
    node = linker.get_node(NodeType.chord, node_id)
    ft = node.serialized_finger_table

    echo(f"node.{NodeType(node.node_type).name}.{node.id} finger table =>")
    for x in ft:
        echo(f"\t{x}")
    echo()


def echo_finger_tables(linker: Linker):
    nodes = linker.get_nodes(NodeType.chord)
    nodes = sorted(nodes)
    for node_id in nodes:
        echo_finger_table(node_id, linker)


@app.command()
def start_name_service():
    uri, daemon, _ = start_ns(host=HOST, port=PORT)
    echo(f"NS running on {uri.location}")
    echo(f"URI => {uri.protocol}:{uri.object}@{uri.location}")
    daemon.requestLoop()


@app.command()
def finger_table(
    id: int = typer.Argument(
        None,
        help="Node id of the desired finger table. If no node is provided then all finger tables will be printed.",
    )
):
    linker = Linker(M)

    if id is None:
        echo_finger_tables(linker)
    else:
        id %= linker.MAX
        echo_finger_table(id, linker)


@app.command()
def create_chord_node(
    id: int = typer.Argument(
        None,
        help="New node id. If no node is provided a random aviable identifier will be assigned.",
    ),
    cache_size: int = typer.Argument(
        5,
        help="The cache max size per node.",
    ),
    use_stabilization: bool = typer.Argument(
        True, help="Use periodical stabilization if True."
    ),
):
    linker = Linker(M)

    node_id = linker.get_aviable_chord_identifier() if id is None else id % linker.MAX
    echo(f"Node id => {node_id}")
    anchor_node = linker.get_random_node(NodeType.chord)
    if anchor_node is not None:
        echo(f"Anchor node => {anchor_node.id}")

    node = ChordNode(node_id, linker, cache_size, use_stabilization)
    uri = linker.register_node(node)

    echo(f"Uri => {uri}")
    node.join(anchor_node)

    if anchor_node is None:
        echo(f"Created node {node_id}")
    else:
        echo(f"Created node {node_id} joined to node {anchor_node.id}")
    node.start_loop()


if __name__ == "__main__":
    app()
