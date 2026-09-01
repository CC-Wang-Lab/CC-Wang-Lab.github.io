#!/usr/bin/env python3
"""Make every Chinese detail page match its English twin, apart from `lang`.

He rewrote English pages by hand all afternoon and the Chinese ones stayed on
the machine conversion, so 18 of 27 pairs had drifted: different markers,
different figure rows, different heading levels.

Copying English over loses nothing today, and that is measured rather than
assumed: not one zh page contains a CJK character its en twin lacks. The
Chinese detail pages have always shown English prose, because the slide deck is
English and the import copied one string into both fields.

The day somebody writes real Chinese, this script stops being safe. It refuses
to run if it finds CJK in a zh page that is not in the en page.
"""
import pathlib
import re
import shutil

ROOT = pathlib.Path(r"C:\Dev\_Projects\34-CC-Wang-Lab-Website\CC-Wang-Lab.github.io")
BACKUP = ROOT / "_tmp/zh-before"


def cjk(s: str) -> set[str]:
    return {ch for ch in s if "\u4e00" <= ch <= "\u9fff"}


pairs = []
for fold in ("facilities", "projects"):
    for en in sorted((ROOT / fold).glob("*.md")):
        zh = ROOT / "zh" / fold / en.name
        if zh.is_file():
            pairs.append((en, zh))

# ---- refuse if any Chinese page carries real Chinese ------------------------
blocked = []
for en, zh in pairs:
    extra = cjk(zh.read_text(encoding="utf-8")) - cjk(en.read_text(encoding="utf-8"))
    if extra:
        blocked.append((zh.relative_to(ROOT), "".join(sorted(extra))[:40]))
if blocked:
    print("REFUSING TO RUN. These Chinese pages carry text the English ones do not:")
    for p, chars in blocked:
        print(f"  {p}   {chars}")
    raise SystemExit(1)

BACKUP.mkdir(parents=True, exist_ok=True)
changed = 0
for en, zh in pairs:
    src = en.read_text(encoding="utf-8")
    want = re.sub(r'^lang\s*=\s*"en"\s*$', 'lang = "zh"', src, count=1, flags=re.M)
    if want == src:
        raise SystemExit(f"{en.relative_to(ROOT)} has no `lang = \"en\"` line")
    if zh.read_text(encoding="utf-8") == want:
        continue
    shutil.copyfile(zh, BACKUP / f"{zh.parent.name}__{zh.name}")
    zh.write_text(want, encoding="utf-8")
    changed += 1
    print(f"  mirrored  zh/{zh.parent.name}/{zh.name}")

print(f"\n{changed} of {len(pairs)} Chinese pages rewritten from their English twin")
print(f"originals kept in {BACKUP.relative_to(ROOT)}")
