from pdf_translator.textutil import is_single_word


def test_single_word():
    assert is_single_word("ubiquitous")
    assert is_single_word("self-driving")
    assert not is_single_word("machine learning")
    assert not is_single_word("Hello, world.")
    assert not is_single_word("a" * 40)
