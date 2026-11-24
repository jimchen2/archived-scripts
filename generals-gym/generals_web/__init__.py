"""Play ``generals_jax`` in a browser.

This is a tiny, dependency-free web front-end for the JAX simulator: a
``http.server`` based JSON API wrapping :class:`generals_jax.GeneralsEnv`, plus
a canvas client in ``generals_web/static`` that renders the board, hides the
fog and takes **WASD / arrow-key** input exactly like generals.io.

Run it with::

    python -m generals_web            # http://localhost:8000

See ``generals_web/README.md`` for the API and the controls.
"""

from .game import Game, GameSettings, snapshots
from .server import create_server, main

__all__ = ["Game", "GameSettings", "snapshots", "create_server", "main"]
__version__ = "0.1.0"
