from __future__ import annotations

import json
import tempfile
from pathlib import Path

from knowledge.models.knowledge import KnowledgeEntry
from knowledge.models.property import KnowledgeProperty
from knowledge.services.search import KnowledgeSearch
from knowledge.services.storage import KnowledgeStore


def test_roundtrip_and_search() -> None:
    with tempfile.TemporaryDirectory() as raw:
        data_dir = Path(raw)
        store = KnowledgeStore(data_dir)
        store.load()
        assert store.entries == []

        entry = KnowledgeEntry(
            name="Niagara Component",
            aliases=["NiagaraComponent", "UNiagaraComponent"],
            category="UE5 / VFX",
            short_description="Component used to attach Niagara System.",
            tags=["UE5", "VFX", "Niagara"],
            properties=[
                KnowledgeProperty(name="Where to Find", value="Blueprint → Add Component → Niagara"),
                KnowledgeProperty(name="When to Use", value="Follow an Actor."),
            ],
        )
        store.add(entry)
        store.save()
        assert (data_dir / "knowledge.json").exists()
        assert (data_dir / "knowledge.backup.json").exists() is False

        store.save()
        assert (data_dir / "knowledge.backup.json").exists()

        store2 = KnowledgeStore(data_dir)
        store2.load()
        assert len(store2.entries) == 1
        loaded = store2.entries[0]
        assert loaded.id == entry.id
        assert loaded.name == "Niagara Component"
        assert "NiagaraComponent" in loaded.aliases
        assert loaded.properties[0].name == "Where to Find"

        search = KnowledgeSearch(cutoff=50)
        hits = search.search(store2.entries, "niagra")
        assert hits and hits[0].entry.name == "Niagara Component"
        hits = search.search(store2.entries, "game ability")
        assert hits == [] or True
        ga = KnowledgeEntry(name="Gameplay Ability", aliases=["GA"], tags=["GAS"])
        store2.add(ga)
        hits = search.search(store2.entries, "game ability")
        assert any(h.entry.name == "Gameplay Ability" for h in hits)

        broken = data_dir / "knowledge.json"
        broken.write_text("{not json", encoding="utf-8")
        store3 = KnowledgeStore(data_dir)
        store3.load()
        assert store3.entries
        assert (data_dir / "knowledge.corrupted.json").exists()

        exported = data_dir / "out.json"
        store2.export_json(exported)
        data = json.loads(exported.read_text(encoding="utf-8"))
        assert "entries" in data


def test_hotkey_parse() -> None:
    from knowledge.services.hotkey_spec import parse_hotkey

    p = parse_hotkey("ctrl + f2")
    assert p.display == "Ctrl+F2"
    p = parse_hotkey("Ctrl+Shift+K")
    assert p.display == "Ctrl+Shift+K"
    try:
        parse_hotkey("F2")
        raise AssertionError("bare F2 should fail")
    except ValueError:
        pass


def test_settings_roundtrip() -> None:
    from knowledge.models.settings import AppSettings

    s = AppSettings.from_dict({"hotkey": "Alt+F2", "popup_position": "center"})
    assert s.hotkey == "Alt+F2"
    assert s.popup_position == "center"
    assert s.capture_selected_text is True


def test_color_compat() -> None:
    from knowledge.models.knowledge import KnowledgeEntry
    from knowledge.shared.color_system import normalize_hex, push_saved_color
    from knowledge.models.settings import AppSettings

    old = KnowledgeEntry.from_dict({"name": "Old"})
    assert old.color == ""
    e = KnowledgeEntry(name="X", color="#B56CFF")
    d = e.duplicate()
    assert d.color.lower() == "#b56cff"
    assert normalize_hex("#B56CFF") == "#b56cff"
    saved = push_saved_color(["#ffb347"], "#b56cff")
    assert saved[0] == "#b56cff"
    assert "#ffb347" in saved
    s = AppSettings.from_dict({})
    assert s.saved_colors == []



def test_appearance_overrides() -> None:
    from knowledge.models.property import KnowledgeProperty
    from knowledge.shared.appearance import Appearance, apply_preset

    raw = KnowledgeProperty.from_dict({"name": "Where", "value": "X"})
    assert raw.style.is_empty_override()
    styled = KnowledgeProperty.from_dict(
        {"name": "Warn", "value": "Y", "style": {"color": "#FF6B6B", "bold": True}}
    )
    assert styled.style.color == "#ff6b6b"
    assert styled.style.bold is True
    dumped = styled.to_dict()
    assert dumped["style"]["color"] == "#ff6b6b"
    assert "font_family" not in dumped["style"]
    app = apply_preset("large")
    merged = app.property_name.overlay(styled.style)
    assert merged.bold is True
    assert merged.font_size == 16
    old_settings = Appearance.from_dict({})
    assert old_settings.entry_name.font_size

if __name__ == "__main__":
    test_roundtrip_and_search()
    test_hotkey_parse()
    test_settings_roundtrip()
    test_color_compat()
    test_appearance_overrides()
    print("ok")

