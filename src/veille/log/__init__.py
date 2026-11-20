"""Configuration des logs (console et fichier)."""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(
<<<<<<< ours
    project_name: str,
    log_dir: Path = Path("logs"),
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Configure le logger du projet, sans doublon de handlers si déjà configuré.

    Parameters
    ----------
    project_name : str
        Nom du logger et préfixe du fichier de log.
    log_dir : Path
        Dossier des fichiers de log, créé si absent.
    level : int
        Niveau de log.

    Returns
    -------
    logging.Logger
        Logger du projet.
    """
    logger = logging.getLogger(project_name)
    if logger.handlers:
        return logger

=======
    project_name: str, log_dir: Path = Path("logs"), level: int = logging.INFO
) -> logging.Logger:
>>>>>>> theirs
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{project_name}_{timestamp}.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
