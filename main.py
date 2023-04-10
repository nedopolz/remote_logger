import click

from controller import Controller


@click.command()
@click.option("--docker-image", help="A name of a Docker image", required=True)
@click.option(
    "--bash-command",
    help="A bash command (to run inside the Docker image)",
    required=True,
)
@click.option(
    "--aws-cloudwatch-group", help="A name of an AWS CloudWatch group", required=True
)
@click.option(
    "--aws-cloudwatch-stream", help="A name of an AWS CloudWatch stream", required=True
)
@click.option("--aws-access-key-id", help="AWS access key id", required=True)
@click.option("--aws-secret-access-key", help="AWS secret access key", required=True)
@click.option("--aws-region", help="A name of an AWS region", required=True)
def run(**kwargs):
    """Simple program that sends container output to given AWS CloudWatch"""
    c = Controller(**kwargs)
    print(c.run())


if __name__ == "__main__":
    run()
