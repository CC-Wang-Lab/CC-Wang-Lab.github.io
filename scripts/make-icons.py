"""
Build the favicon set from the lab logo.

WHY THE ICON IS A CROP, NOT THE WHOLE MARK
logo-mark.png is 1594x716, a ratio of 2.2:1. Padded into a square for a 16px
favicon it becomes a seven-pixel smear with no recognisable shape. The central
fan motif is already square, it carries both brand colours, and it still reads
at 16px. That crop is what ships. Checked at 16px, not at 512px.

Run from the repo root after changing the logo:

    python scripts/make-icons.py
"""
from PIL import Image
import os

SRC = "_assets/img/logo-mark.png"
OUT = "_assets/icon"

# The fan motif inside logo-mark.png, with 2% air around it.
CROP = (575, 100, 1055, 640)
PAD = 0.02

# iOS composites an apple-touch-icon onto black, so that one gets a real
# background instead of transparency. The value is --lab-surface from style.css.
IOS_BG = (255, 255, 255, 255)


def squared(src, pad=PAD, bg=(0, 0, 0, 0)):
    w, h = src.size
    side = int(max(w, h) * (1 + 2 * pad))
    out = Image.new("RGBA", (side, side), bg)
    out.paste(src, ((side - w) // 2, (side - h) // 2), src)
    return out


def main():
    mark = Image.open(SRC).convert("RGBA")
    icon = squared(mark.crop(CROP))
    solid = squared(mark.crop(CROP), bg=IOS_BG)

    def write(img, size, name):
        img.resize((size, size), Image.LANCZOS).save(os.path.join(OUT, name))

    write(icon, 16, "favicon-16x16.png")
    write(icon, 32, "favicon-32x32.png")
    write(icon, 96, "favicon-96x96.png")
    write(solid, 180, "apple-touch-icon.png")
    write(icon, 192, "android-chrome-192x192.png")
    write(icon, 512, "android-chrome-512x512.png")
    write(solid, 150, "mstile-150x150.png")

    icon.resize((256, 256), Image.LANCZOS).save(
        os.path.join(OUT, "favicon.ico"),
        sizes=[(16, 16), (32, 32), (48, 48)],
    )
    print("wrote the icon set to", OUT)


if __name__ == "__main__":
    main()
