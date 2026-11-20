from datetime import date, timedelta
from pathlib import Path

import pytest

from veille.data import seen as seen_module
from veille.data.seen import load_seen, prune, save_seen

TODAY = date(2026, 11, 20)


def test_load_seen_fichier_absent_renvoie_un_historique_vide(tmp_path: Path) -> None:
    assert load_seen(tmp_path / "seen.json") == {}


def test_save_puis_load_seen_conserve_l_historique(tmp_path: Path) -> None:
    path = tmp_path / "seen.json"
    seen = {"https://b.com/x": date(2026, 11, 19), "https://a.com/y": TODAY}

    save_seen(path, seen)

    assert load_seen(path) == seen
    assert not path.with_suffix(".tmp").exists()


def test_save_seen_echec_laisse_le_fichier_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "seen.json"
    save_seen(path, {"https://a.com/y": TODAY})
    before = path.read_text(encoding="utf-8")

    def boom(*_: object) -> None:
        raise OSError("disque plein")

    monkeypatch.setattr(seen_module.os, "replace", boom)
    with pytest.raises(OSError):
        save_seen(path, {"https://autre.com": TODAY})

    assert path.read_text(encoding="utf-8") == before


def test_prune_retire_les_entrees_de_plus_de_90_jours() -> None:
    seen = {
        "https://old.com": TODAY - timedelta(days=91),
        "https://limite.com": TODAY - timedelta(days=90),
        "https://recent.com": TODAY,
    }

    assert set(prune(seen, TODAY)) == {"https://limite.com", "https://recent.com"}
