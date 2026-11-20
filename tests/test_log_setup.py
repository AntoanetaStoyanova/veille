import logging
from collections.abc import Iterator
from pathlib import Path

import pytest

from veille.log import setup_logging

NAME = "veille-test-log"


@pytest.fixture(autouse=True)
def _clean_logger() -> Iterator[None]:
    yield
    logger = logging.getLogger(NAME)
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)


def test_setup_logging_cree_un_fichier_et_deux_handlers(tmp_path: Path) -> None:
    logger = setup_logging(NAME, tmp_path)

    assert len(logger.handlers) == 2
    assert len(list(tmp_path.glob(f"{NAME}_*.log"))) == 1


def test_setup_logging_appele_deux_fois_n_ajoute_pas_de_doublons(
    tmp_path: Path,
) -> None:
    setup_logging(NAME, tmp_path)
    logger = setup_logging(NAME, tmp_path)

    assert len(logger.handlers) == 2
