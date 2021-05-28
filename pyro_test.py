# saved as greeting-server.py
import Pyro5.api
import typer

app = typer.Typer()


@Pyro5.api.expose
class User:
    def __init__(self, name):
        self._name = name

    def name(self):
        return self._name


@app.command()
def serve(name: str):
    daemon = Pyro5.api.Daemon()  # make a Pyro daemon
    ns = Pyro5.api.locate_ns()  # find the name server
    uri = daemon.register(User(name), f"user.{name}")
    ns.register(f"user.{name}", uri, metadata=["user"])

    print("Ready.")
    daemon.requestLoop()


@app.command()
def connect(name: str):
    greeting_maker = Pyro5.api.Proxy(
        f"PYRONAME:user.{name}"
    )  # use name server object lookup uri shortcut
    print(greeting_maker.name())


if __name__ == "__main__":
    app()
