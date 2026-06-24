from pdf_translator.textutil import is_single_word


def test_single_word():
    assert is_single_word("ubiquitous")
    assert is_single_word("self-driving")
    assert not is_single_word("machine learning")
    assert not is_single_word("Hello, world.")
    assert not is_single_word("a" * 40)


def test_strip_edge_punct():
    from pdf_translator.textutil import strip_edge_punct, is_single_word
    assert strip_edge_punct("world.") == "world"
    assert strip_edge_punct("cheated,") == "cheated"
    assert strip_edge_punct("(BJP)") == "BJP"
    assert strip_edge_punct("“quote”") == "quote"
    assert strip_edge_punct("self-driving") == "self-driving"   # internal kept
    assert strip_edge_punct("Mr Modi's Party.") == "Mr Modi's Party"
    # trailing punctuation no longer breaks single-word detection
    assert is_single_word(strip_edge_punct("ubiquitous;"))
