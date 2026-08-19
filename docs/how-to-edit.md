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
tier          = "phd"               # see the table below
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

**Which section a person lands in** is decided by `tier`:

| `tier` | Section on the People page | Shown as |
|---|---|---|
| `pi` | at the top | a large block, one person only |
| `lead` | Research leads | photo card |
| `postdoc` | Postdoctoral researchers | photo card |
| `phd` | PhD students | photo card |
| `msc` | MSc students | photo card |

**Everyone appears twice**: once as a photo card in their own section, and once in the
"Everyone in the lab" table at the bottom of the page. The table is the index — one line each,
for finding a name without scrolling past forty photographs.

Anyone with `status = "alumni"` goes to the Alumni page instead, whatever their tier.

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

### Give a person their own page

Copy `people/placeholder-phd-1.md` to `people/<your-id>.md` and
`zh/people/placeholder-phd-1.md` to `zh/people/<your-id>.md`. Change
`person = "..."` in both to your id from `team.toml`, then write.

Everything in the page header — photo, name, role, topic, email, Scholar link —
comes from your row in `team.toml`. Do not repeat it in the page.

**The card becomes a link the moment the file exists.** There is no flag to set
and nothing to remember. A person with no page yet is a plain card, not a dead
link, so the site is never broken by a page that has not been written.

Any project in `projects.toml` naming you as its `student` appears at the bottom
of your page automatically.

---

## Turn the contact form on

The form at `/contact/` works today, but it does not send the email itself. It
opens the visitor's mail program with every answer filled in, and they press
send. That needs no account anywhere, which is why it is the default.

**To make it send by itself, two steps.**

1. Create a free account at [formspree.io](https://formspree.io) or
   [web3forms.com](https://web3forms.com) and point it at `ccwang@nycu.edu.tw`.
2. Paste the endpoint into `config.md`:

```
form_endpoint   = "https://formspree.io/f/XXXXXXXX"
form_access_key = ""                 # Web3Forms only; Formspree needs nothing here
```

That one line is the whole switch. The form's markup does not change, and the
visitor stops leaving the page: the reply appears underneath the button.

To change what the form asks, edit the `[form]` section of `_data/ui.toml`.
Both languages sit on adjacent lines, as everywhere else.

## Add a project

This is the one your professor asked for: every experiment gets its own page,
written by the person doing the work.

**Two steps.**

**Step 1 — add a row to `_data/projects.toml`:**

```toml
[[project]]
id       = "cold-plate-high-flux"    # lowercase, no spaces. Becomes the web address.
weight   = 3                          # sorts the grid inside its area, lowest first
image    = "/assets/img/projects/cold-plate-high-flux.jpg"
student  = "chen-mei-ling"            # must be an id already in team.toml
area     = "electronics-cooling"      # must be an id already in research.toml
title_en = "Cold-plate design for high heat flux"
title_zh = "高熱通量冷板設計"
lead_en  = "One or two sentences. What is measured or built, and what question it answers."
lead_zh  = "一至兩句話，說明量測或建置什麼、以及回答什麼問題。"
```

**Step 2 — write the page.** Copy `projects/placeholder-project.md` to
`projects/cold-plate-high-flux.md`, and copy the Chinese one to
`zh/projects/cold-plate-high-flux.md`. Change `project = "..."` in both to your new id, then
write. It is ordinary Markdown: headings, paragraphs, lists, images.

**Images.** Put them in `_assets/img/projects/<your-id>/` and use them like this:

```markdown
![](/assets/img/projects/cold-plate-high-flux/rig.jpg)
```

The cover image on the card must be **16:9** and under **250 KB**. Anything larger slows the page
for everyone.

**Where it appears.** The grid at `/projects/` holds every project, three across on a wide screen.
The `area` you gave it becomes a filter button above the grid, and that button appears on its own —
you do not add it anywhere. Projects are ordered by research area first, then by `weight` inside
the area.

**If you mistype the `student` or `area` id, the build stops with a message naming the bad id.**
That is deliberate. A silent blank card is worse than a failed build.

**What you never write:** the researcher name, the photo, the research-area label. All three are
looked up from the ids, so they can never disagree with the People page.

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
| Edit HTML to add a person, a paper or a project | The two language versions will drift apart within months. |
| Put a company logo on the site without written permission | Most of our industrial work is under NDA. |
| Upload a video larger than 1 MB to `_assets/video/` | GitHub allows 100 GB of traffic a month. A big file burns it. |
| Delete `last_verified` from a person | It is the only check that keeps the team page honest. |
