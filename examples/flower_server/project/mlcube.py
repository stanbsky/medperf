"""MLCube handler file"""

import typer
import yaml
from typing import List, Tuple
from flwr.common import Metrics
from flwr.server import start_server, ServerConfig
from flwr.server.strategy import FedAvg

app = typer.Typer()


def weighted_average(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    # Multiply accuracy of each client by number of examples used
    accuracies = [num_examples * m["accuracy"] for num_examples, m in metrics]
    examples = [num_examples for num_examples, _ in metrics]

    # Aggregate and return custom metric (weighted average)
    return {"accuracy": sum(accuracies) / sum(examples)}


class Server(object):

    @staticmethod
    def run(
            params_file: str, out_path: str
    ) -> None:
        with open(params_file, "r") as f:
            params = yaml.full_load(f)

        allowed_strategies = [
            "FedAvg"
        ]

        if params["strategy"] not in allowed_strategies:
            print("The specified strategy couldn't be found")
            exit(1)
        else:
            strategy = FedAvg(evaluate_metrics_aggregation_fn=weighted_average)
        history = start_server(
            server_address=params["server_address"],
            config=ServerConfig(num_rounds=params["rounds"]),
            strategy=strategy,
        )
        # TODO: write history to pickle
        # TODO: write model weights to output file


@app.command("run")
def run(
        params_file: str = typer.Option(..., "--parameters_file"),
        out_path: str = typer.Option(..., "--output_path"),
):
    Server.run(params_file, out_path)


@app.command("hotfix")
def hotfix():
    # NOOP command for typer to behave correctly. DO NOT REMOVE OR MODIFY
    pass


if __name__ == "__main__":
    app()
