# Data files — the one hard rule of this repo

**Never write HTML for a person, a paper, a news item, a research area, a capability or a sector.**

*Why: the lab has 50 to 60 people and the site is bilingual. Hand-written HTML means one language
gets updated and the other does not. Within a year the two sites disagree, and nobody notices.*

Every list is generated at build time by an `hfun_*` function in `utils.jl` from a file in `_data/`.

| File | Generator | Appears on |
|---|---|---|
| `ui.toml` | `hfun_ui` | Every interface string on the site, both languages |
| `research.toml` | `hfun_research_cards`, `hfun_research_full` | Home, Research |
| `capabilities.toml` | `hfun_capabilities`, `hfun_capabilities_brief` | Home, Capabilities |
| `sectors.toml` | `hfun_sectors` | Home |
| `team.toml` | `hfun_team_pi`, `_leads`, `_members`, `_alumni` | Home, Team, Alumni |
| `publications.toml` | `hfun_publications` | Publications |
| `news.toml` | `hfun_news` | Home (newest 3), News |

## Bilingual fields

Every row carries both languages in the same row, with an `_en` and a `_zh` suffix:

```toml
title_en = "Electronics & AI Cooling"
title_zh = "電子與 AI 散熱"
```

`pick(d, "title")` in `utils.jl` picks the right one from the page's `lang`. One row, both sites.
It is not possible to update English and forget Chinese, because they are on adjacent lines.

## The staleness check

Every `[[person]]` row must carry:

```toml
status        = "current"      # or "alumni"
last_verified = "2026-08-19"
```

The build prints a warning when a `current` person has not been verified for **12 months**:

```
┌ Warning: team.toml: 'someone' last verified 2025-06-01, over 12 months ago
```

*Why: generating a page from a data file does not stop the data going out of date. If a postdoc
leaves and nobody edits the file, Franklin will reproduce the wrong information perfectly, forever.
A lab that claims 20+ active industrial projects and still lists people who left two years ago
does itself more damage than having no team page at all.*

## A line starting with a year becomes a numbered list

Markdown reads `2010.` at the start of a line as an ordered-list marker. It cost one round on
`people/cc-wang.md`: a paragraph about ITRI wrapped so that "2010. That is the part of the
record..." began a line, and Franklin broke one paragraph into three indented fragments.

**Never let a line begin with digits followed by a full stop** unless a numbered list is what you
want. Reflow the line, or move the year one word later. The failure looks like bad CSS, not like
Markdown, which is why it took a screenshot to see.

## Adding a language later

Add a third suffix (`_ja`, say), add the folder, extend `NAV` and `prefix()` in `utils.jl`.
Nothing else changes, because no string is hard-coded in a layout.
