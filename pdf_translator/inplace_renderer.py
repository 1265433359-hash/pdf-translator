import fitz


def render_inplace(page, block_translations, font_path=None, zoom=1.5):
    """就地替换渲染：抹掉原文区域，在原位写入中文译文。

    block_translations: list of (fitz.Rect, zh_text)。
    对每个块 redact 原文 → 在 rect 内 insert_textbox 写中文，
    字号从 11 起逐级缩小到 5 直到放得下，返回该页的 Pixmap。
    fontname 用 PyMuPDF 内置简中字体 "china-s"（本机已验证可用）；
    如需自带 TTF 可通过 font_path 指定。
    """
    for rect, _ in block_translations:
        page.add_redact_annot(rect, fill=(1, 1, 1))
    page.apply_redactions()
    for rect, zh in block_translations:
        size = 11
        while size >= 5:
            rc = page.insert_textbox(rect, zh, fontsize=size, fontname="china-s",
                                     fontfile=font_path, align=0)
            if rc >= 0:
                break
            size -= 1
    return page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
