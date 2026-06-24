from pdf_translator.text_preprocessor import paragraphs_from_blocks


def test_dehyphenate_and_join():
    blocks = [(0, 100, 300, 120, "This is an evalu-\nation of the\nmethod.", 0, 0)]
    paras = paragraphs_from_blocks(blocks)
    assert paras == ["This is an evaluation of the method."]


def test_two_column_order():
    blocks = [
        (300, 100, 560, 120, "Right column first line", 1, 0),
        (0, 100, 260, 120, "Left column first line", 0, 0),
    ]
    paras = paragraphs_from_blocks(blocks)
    assert paras[0].startswith("Left")  # 左栏先
