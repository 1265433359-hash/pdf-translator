import re


def _clean(text: str) -> str:
    text = re.sub(r"-\n", "", text)          # 去连字符断行
    text = re.sub(r"\s*\n\s*", " ", text)    # 行合并
    return re.sub(r"\s+", " ", text).strip()


def paragraphs_from_blocks(blocks, header_footer_max_len=3):
    text_blocks = [b for b in blocks if b[6] == 0 and b[4].strip()]
    if not text_blocks:
        return []
    page_mid = sorted((b[0] + b[2]) / 2 for b in text_blocks)[len(text_blocks) // 2]
    left = [b for b in text_blocks if (b[0] + b[2]) / 2 < page_mid]
    right = [b for b in text_blocks if (b[0] + b[2]) / 2 >= page_mid]
    ordered = (
        sorted(left, key=lambda b: b[1]) + sorted(right, key=lambda b: b[1])
        if right
        else sorted(text_blocks, key=lambda b: b[1])
    )
    paras = []
    for b in ordered:
        c = _clean(b[4])
        if len(c.split()) <= header_footer_max_len:  # 丢极短块（页眉页脚页码）
            continue
        paras.append(c)
    return paras
