"""MLCube handler file"""

import typer
from flwr.server import start_server, ServerConfig

app = typer.Typer()


class Server(object):

    @staticmethod
    def run(
            server_address,
            rounds,
            strategy,
    ):
        history = start_server(
            server_address=server_address,
            config=ServerConfig(num_rounds=rounds),
            strategy=strategy,
        )
        # TODO: write history to pickle
        # TODO: write model weights to output file


@app.command("run")
def run(
        server_address: str = typer.Option(..., "--server-address"),
        rounds: int = typer.Option(..., "--rounds"),
        strategy: str = typer.Option(..., "--strategy"),
):
    Server.run(server_address, rounds=rounds, strategy=strategy)


@app.command("hotfix")
def hotfix():
    # NOOP command for typer to behave correctly. DO NOT REMOVE OR MODIFY
    pass


if __name__ == "__main__":
    app()
