# How to edit this website

**You never write HTML.** Every list on the site is built from a small text file. Add a line, push,
and the page updates itself — in English and in Chinese.

All the files live in the `_data/` folder. They are `.toml` files: plain text you can open in
Notepad, TextEdit or VS Code.

---

## The rule for every file

Each entry has an English field and a Chinese field, side by side:

```toml
title_en = "Electronics & AI Cooling"
title_zh = "電子與 AI 散熱"
```

**Fill in both.** They sit on next-door lines so you cannot forget one.

---

## Add a person

Open `_data/team.toml`. Copy an existing block and change it.

```toml
[[person]]
id            = "chen-mei-ling"     # anything unique, lowercase, no spaces
tier          = "member"            # "lead" for a large card, "member" for a row
status        = "current"           # "current" or "alumni"
last_verified = "2026-08-19"        # today's date. Required.
name_en       = "Mei-Ling Chen"
name_zh       = "陳美玲"
role_en       = "PhD Student"
role_zh       = "博士生"
topic_en      = "Immersion cooling of server boards"
topic_zh      = "伺服器板浸沒式冷卻"
photo         = "/assets/img/team/chen-mei-ling.jpg"   # optional
email         = "..."                                  # optional
```

**About `last_verified`.** Put today's date. Once a year the site build will start printing a
warning for anyone whose date is over twelve months old. That warning is the only thing standing
between this page and a list of people who left years ago.

**When someone leaves**, do not delete them. Change two lines:

```toml
status    = "alumni"
left_year = 2026
```

They move to the Alumni page automatically.

**Photos.** Square, at least 400 × 400 pixels, JPEG. Put the file in `_assets/img/team/`.
Leave `photo` out and a grey silhouette appears instead — that is fine.

---

## Add a news item

Open `_data/news.toml`.

```toml
[[item]]
date     = 2026-09-14        # no quotes. The site sorts by this.
tag      = "paper"           # paper, award, facility, project, talk
title_en = "Paper accepted in the International Journal of Heat and Mass Transfer"
title_zh = "論文獲國際期刊接受"
body_en  = "One or two sentences. Say what happened and why an outsider should care."
body_zh  = "一至兩句話，說明發生什麼事、以及為何值得關注。"
```

The three newest items appear on the home page. All of them appear on the News page.

**Delete the three PLACEHOLDER items before the site goes public.**

---

## Add a publication

Open `_data/publications.toml`.

```toml
[[paper]]
theme     = "electronics"    # must match a theme id in the same file
title     = "Full paper title, exactly as published"
venue     = "International Journal of Heat and Mass Transfer"
year      = 2026
citations = 12               # optional. Leave it out for a recent paper.
```

The theme ids are at the top of the file: `electronics`, `two-phase`, `heat-exchangers`,
`hvacr`, `nanofluids`, `energy-ai`.

**Leave `citations` out for anything recent.** A "3 citations" label next to important new work
reads worse than no number at all.

---

## Change a word on the site

Open `_data/ui.toml`. Every button, heading and label on the site is in this one file, in both
languages. Change it there and it changes everywhere, on both language versions.

---

## See your change before pushing

```bash
julia --project=. -e 'using Franklin; serve()'
```

Open http://localhost:8000. Edit a file, save, and the browser updates by itself.
Press `Ctrl+C` in the terminal to stop.

If a change does not appear, stop the server and start it again with:

```bash
julia --project=. -e 'using Franklin; serve(clear=true)'
```

---

## Publish

```bash
git add -A
git commit -m "add three news items for September"
git push
```

Wait about three minutes. The site rebuilds itself and goes live at
https://cc-wang-lab.github.io/

If a green tick appears next to your commit on GitHub, it worked. A red cross means the build
failed — click it to see why, and ask for help rather than pushing again.

---

## Things you must not do

| Do not | Because |
|---|---|
| Edit any file in `__site/` | It is deleted and rebuilt every time. Your change disappears. |
| Edit HTML to add a person or a paper | The two language versions will drift apart within months. |
| Put a company logo on the site without written permission | Most of our industrial work is under NDA. |
| Upload a video larger than 1 MB to `_assets/video/` | GitHub allows 100 GB of traffic a month. A big file burns it. |
| Delete `last_verified` from a person | It is the only check that keeps the team page honest. |
