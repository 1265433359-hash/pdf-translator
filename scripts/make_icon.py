"""Render the app icon to data/icon.png + data/icon.ico (multi-size), using
Pillow + a Windows CJK font file directly (avoids headless Qt font issues).
Run: python scripts/make_icon.py"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

R = 4  # supersample factor for crisp edges
W = 256 * R
U = W / 96.0  # one unit of the 96-space design grid, in device pixels

TILE = "#b3793f"
B1, B1T = "#fffaf2", "#a8652e"   # front bubble fill, 文 color
B2, B2T = "#f1ddc2", "#875327"   # back bubble fill, A color

FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
]


def _font(px):
    for f in FONT_CANDIDATES:
        if Path(f).exists():
            return ImageFont.truetype(f, px)
    return ImageFont.load_default()


def _bubble(d, x, y, w, h, rad, fill, tail):
    d.rounded_rectangle((x * U, y * U, (x + w) * U, (y + h) * U),
                        radius=rad * U, fill=fill)
    d.polygon([(p[0] * U, p[1] * U) for p in tail], fill=fill)


def main():
    data = Path(__file__).resolve().parent.parent / "data"
    data.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, W, W), radius=22 * U, fill=TILE)
    # front bubble + tail, then back bubble + tail (coords in 96-space)
    _bubble(d, 20, 28, 36, 27, 7, B1, [(28, 55), (28, 64), (38, 55)])
    d.text((38 * U, 41 * U), "文", font=_font(int(20 * U)), fill=B1T, anchor="mm")
    _bubble(d, 46, 44, 31, 25, 7, B2, [(69, 69), (69, 77), (60, 69)])
    d.text((61 * U, 56 * U), "A", font=_font(int(19 * U)), fill=B2T, anchor="mm")

    img = img.resize((256, 256), Image.LANCZOS)
    img.save(str(data / "icon.png"))
    img.save(str(data / "icon.ico"),
             sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("wrote", data / "icon.png", "and", data / "icon.ico")


if __name__ == "__main__":
    main()
