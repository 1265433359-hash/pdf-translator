def export_csv(rows, out_path):
    lines = []
    for r in rows:
        back_parts = []
        if r.get("phonetic"): back_parts.append(f"/{r['phonetic']}/")
        back_parts += r.get("meanings", [])
        back_parts += r.get("examples", [])
        back = "<br>".join(back_parts)
        lines.append(f"{r['word']}\t{back}")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
