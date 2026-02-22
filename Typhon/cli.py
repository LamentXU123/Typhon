import click
import sys
from pathlib import Path

_root = str(Path(__file__).parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

@click.group()
def cli():
    pass

@cli.command()
def webui():
    from Typhon.webui.app import app
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)

if __name__ == "__main__":
    cli()