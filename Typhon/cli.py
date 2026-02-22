import click
import sys
from pathlib import Path
@click.group()
def cli():
    pass

@cli.command()
def webui():
    sys.path.insert(0, str(Path(__file__).parent))
    from webui.app import app
    app.run()

if __name__ == "__main__":
    cli()