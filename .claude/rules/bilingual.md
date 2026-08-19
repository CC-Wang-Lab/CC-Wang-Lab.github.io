# Bilingual pages

Franklin.jl has **no i18n support at all**. No locale system, no translation file, no language-aware
routing. This site does it with mirrored folders and three helpers.

## Layout

```
research.md      ->  /research/       lang = "en"   (the global default in config.md)
zh/research.md   ->  /zh/research/    lang = "zh"
```

Every Chinese page carries `lang = "zh"` in its front matter. That single variable drives the
`<html lang="zh-Hant">` attribute, the navigation labels, the URL prefix and every generated string.

## The three helpers — use them, always

| Helper | Gives | Never write instead |
|---|---|---|
| `{{url research}}` | `/research/` or `/zh/research/` | `href="/research/"` |
| `{{url home}}` | `/` or `/zh/` | `href="/"` |
| `{{ui nav research}}` | the label in the page's language | the English word |

*Why `{{url}}` matters: a hard-coded `/research/` works in English and silently throws every
Chinese reader back onto the English site. It is invisible in testing unless you click it while
reading Chinese.*

## Adding a page

1. Write `newpage.md` using `{{url}}` and `{{ui}}` for everything that is not body prose.
2. Copy it to `zh/newpage.md`, change `lang` to `"zh"`, translate the front-matter `title` and
   `descr`, and translate any Markdown prose.
3. Add the strings it needs to `_data/ui.toml`, both languages.
4. Add it to `const NAV` in `utils.jl` if it belongs in the navigation.

Pages whose content is entirely generated (Research, Capabilities, Team, News, Publications) are a
**pure copy** with the `lang` line changed. Only Industry and Contact carry hand-written prose that
must be translated by hand.

## The font trap

**ET Book has no Chinese glyphs.** Without a CJK face in the stack, every Chinese page renders as
empty boxes, and it looks fine to anyone testing in English.

```css
font-family: "et-book", "Noto Serif TC", "Times New Roman", Times, serif;
```

Noto Serif TC comes from Google Fonts with `&display=swap`. Google splits CJK faces by
`unicode-range`, so an English-only page never downloads the Chinese subsets.

## Still to do

The Chinese on this site was written by Claude and **must be reviewed by a native Traditional
Chinese speaker before launch**. Taiwanese engineering usage differs from mainland usage, and a
wrong technical term is worse than English.
