"""Veille quotidienne : collecte, tri et résumé d'articles envoyés par mail."""

from beartype.claw import beartype_this_package

beartype_this_package()

# Après beartype : le contrôle ne couvre que les modules importés ensuite.
from veille.bin.pipeline import main  # noqa: E402

__version__ = "0.1.0"
__all__ = ["main"]
