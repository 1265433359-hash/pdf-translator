def _paths(items):
    return [it["path"] for it in items]


def test_recents_add_dedupe_and_order(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    from pdf_translator import recents
    assert recents.all_recents() == []
    recents.add_recent("a.pdf", ts=1)
    recents.add_recent("b.pdf", ts=2)
    recents.add_recent("a.pdf", ts=3)  # re-open promotes to front, no dupe
    assert _paths(recents.all_recents()) == ["a.pdf", "b.pdf"]
    recents.remove_recent("a.pdf")
    assert _paths(recents.all_recents()) == ["b.pdf"]
    recents.clear()
    assert recents.all_recents() == []


def test_recents_cap_and_ts(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    from pdf_translator import recents
    for i in range(30):
        recents.add_recent(f"f{i}.pdf", ts=i)
    items = recents.all_recents()
    assert len(items) == recents.LIMIT
    assert items[0]["path"] == "f29.pdf"   # most recent first
    assert items[0]["ts"] == 29.0


def test_recents_tolerates_old_string_format(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    import json
    from pdf_translator import recents, paths
    (paths.config_dir() / "recents.json").write_text(
        json.dumps(["old1.pdf", "old2.pdf"]), encoding="utf-8")
    assert _paths(recents.all_recents()) == ["old1.pdf", "old2.pdf"]
