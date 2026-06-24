def test_recents_add_dedupe_and_order(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    from pdf_translator import recents
    assert recents.all_recents() == []
    recents.add_recent("a.pdf")
    recents.add_recent("b.pdf")
    recents.add_recent("a.pdf")  # re-open promotes to front, no dupe
    assert recents.all_recents() == ["a.pdf", "b.pdf"]
    recents.remove_recent("a.pdf")
    assert recents.all_recents() == ["b.pdf"]


def test_recents_cap(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    from pdf_translator import recents
    for i in range(20):
        recents.add_recent(f"f{i}.pdf")
    assert len(recents.all_recents()) == recents.LIMIT
    assert recents.all_recents()[0] == "f19.pdf"  # most recent first
