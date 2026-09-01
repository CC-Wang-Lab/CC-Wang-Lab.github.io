# Logo files still needed

**This file is generated** by `scripts/prepare-partner-logos.py`.

**72 of 73 organisations have a logo. 1 does not**, and render as their name in text until a
file arrives. The strip works either way, so nothing is blocked.

| Organisation | 中文 |
|---|---|
| Chun-Hung Technology | 長宏科技 |

## How to add one

1. Drop the file in `../_internal-docs/logo-originals/`. A PNG with a
   transparent background is fine; a real SVG is better.
2. Add a `[[logo]]` row to `../_internal-docs/partner-logo-map.toml`
   naming the organisation, its slug and that file.
3. Run `python scripts/prepare-partner-logos.py`. It sizes the logo,
   writes the asset, fills `logo`/`w`/`h` in `_data/partners.toml` and
   rewrites `SOURCES.md`.
4. Run `python scripts/check-partner-logos.py`. It fails a logo that
   disappears in either theme.

**Look at every file before accepting it.** Searching by name is
unreliable: "ASE Group logo" returned the European Space Agency banner,
"Lite-On logo" an unrelated mark reading "TL", and "Google logo" the
2012 Google Play logo. All three would have been visible errors.

## Names still to be confirmed by the lab

These 13 rows carry `check = true`. Each name was read off the
logo, or off the file name where the mark carries no words, and could
not be settled against a public record.

| Organisation | 中文 |
|---|---|
| Metal Industries Research & Development Centre | 金屬工業研究發展中心 |
| National Chung-Shan Institute of Science and Technology | 國家中山科學研究院 |
| AVC | 奇鋐科技 |
| Rayvatek | 銳澤 |
| Sakura | 櫻花 |
| Cryomax Cooling System | 誠加興業 |
| Chun-Hung Technology | 長宏科技 |
| Jentech Precision | 健策精密 |
| Vigour Group | 偉喬集團 |
| Ritex Machinery | Ritex |
| Hon.Precision | 鴻勁精密 |
| SATTI | 超尊科技 |
| Hot Cool | 高揚國際實業 |
