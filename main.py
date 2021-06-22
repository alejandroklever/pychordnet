import typer
from Pyro5.nameserver import start_ns

from dscraping.chord_node import ChordNode
from dscraping.client_node import ClientNode
from dscraping.monitoring import echo
from dscraping.node import Linker, NodeType
from dscraping.scrapper_node import RouterNode

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


def echo_hash_table(node_id: int, linker: Linker):
    node = linker.get_node(NodeType.chord, node_id)
    ht = node.serialized_hash_table_keys

    echo(f"node.{NodeType(node.node_type).name}.{node.id} hash table keys =>")
    for x in ht:
        echo(f"\t{x}")
    echo()


def echo_hash_tables(linker: Linker):
    nodes = linker.get_nodes(NodeType.chord)
    nodes = sorted(nodes)
    for node_id in nodes:
        echo_hash_table(node_id, linker)


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
def hash_table(
    id: int = typer.Argument(
        None,
        help="Node id of the desired finger table. If no node is provided then all finger tables will be printed.",
    )
):
    linker = Linker(M)

    if id is None:
        echo_hash_tables(linker)
    else:
        id %= linker.MAX
        echo_hash_table(id, linker)


@app.command()
def create_chord_node(
    id: int = typer.Argument(
        None,
        help="New node id. If no node is provided a random aviable identifier will be assigned.",
    ),
    cache_size: int = typer.Argument(
        10,
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


@app.command()
def disconnect_chord_node(
    id: int = typer.Argument(
        None,
        help="Node id. If no node is provided a random aviable identifier will be assigned.",
    ),
):
    linker = Linker(M)
    if id is None:
        node = linker.get_random_node(NodeType.chord)
    else:
        node = linker.get_node(NodeType.chord, id)

    if node is None:
        return

    echo(f"Disconnect Node: {node.id}")
    node.disconnect()


@app.command()
def create_router_node():
    linker = Linker(M)
    node = RouterNode(linker)
    echo(f"Node id => {node.id}")
    uri = linker.register_node(node)
    echo(f"Uri => {uri}")
    echo(f"Created node {node.id}. Location: {uri}")
    node.start_loop()


@app.command()
def create_client_node(
    file: typer.FileText = typer.Argument(
        None,
        help="File with the urls for this node to resolve.",
    )
):
    lines = [line if line[-1] != "\n" else line[:-1] for line in file.readlines()]

    linker = Linker(M)
    node = ClientNode(linker, lines)
    echo(f"Client Node id => {node.id}")
    uri = linker.register_node(node)
    echo(f"Uri => {uri}")
    echo(f"Created Client Node {node.id}.\nLocation: {uri}")
    node.start_loop()


@app.command()
def scrap(url: str = typer.Argument(None, help="Url to be scrapped")):
    linker = Linker(M)
    node = ClientNode(linker, [url])
    echo(f"Client Node id => {node.id}")
    uri = linker.register_node(node)
    echo(f"Uri => {uri}")
    echo(f"Created Client Node {node.id}.\nLocation: {uri}")
    node.start_loop()


if __name__ == "__main__":
    app()
