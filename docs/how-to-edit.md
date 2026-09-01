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

Copy `docs/templates/person.en.md` to `people/<your-id>.md` and
`docs/templates/person.zh.md` to `zh/people/<your-id>.md`. Change
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

Right now the form does **not** send. It opens the visitor's own mail program
with the message filled in, addressed to `juliahsieh@nycu.edu.tw`, and they
press send there. That needs no account anywhere, which is why it is the
default rather than a dead button.

**To make it deliver by itself, three steps.**

1. Go to [web3forms.com](https://web3forms.com) and enter
   **`juliahsieh@nycu.edu.tw`**. There is no account and no password — the
   access key arrives by email.
2. Paste the key into `form_access_key` in `config.md`.
3. Set `form_endpoint` to `https://api.web3forms.com/submit`.

```
form_endpoint   = "https://api.web3forms.com/submit"
form_access_key = "the key from the email"
```

**Use Julia's address at step 1, not anyone else's.** Web3Forms delivers to
whichever address created the key. `form_to` in `config.md` does not control
that — it is only used by the mail-program fallback and by the "it did not
send" message. A key made with the wrong address sends the mail somewhere else
and nothing on the site will say so.

Replies go to the visitor automatically, because the form's email box is named
`email` and both services treat that as the reply-to address.

Formspree works too: set `form_endpoint` to `https://formspree.io/f/XXXXXXXX`
and leave `form_access_key` empty. The two services do not use the same hidden
field names, and `utils.jl` emits whichever set the endpoint needs.

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

**Step 2 — write the page.** Copy `docs/templates/project.en.md` to
`projects/cold-plate-high-flux.md`, and copy `docs/templates/project.zh.md` to
`zh/projects/cold-plate-high-flux.md`. Change `project = "..."` in both to your new id,
then write. It is ordinary Markdown: headings, paragraphs, lists, images.

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

## Add an imported facility or project

A record holds the WORDS and the PICTURES. Its page holds the LAYOUT. Keep the source wording
and captions exactly as supplied, and do not upload a complete slide when its individual figures
can be used. This is one complete facility record for `_data/facilities.toml`:

```toml
[[item]]
id            = "example-cold-plate-rig"
area          = "two-phase"                 # an id from research.toml
image         = "/assets/img/test-setups/example-cold-plate-rig/diagram.png"
image_fit     = "contain"                   # "cover" (default) or "contain" for drawings
source_slides = [31, 32]                     # source-slide numbers; not displayed
title_en      = "Example cold-plate test rig"
title_zh      = "範例冷板測試平台"
lead_en       = "One-sentence source summary."
lead_zh       = "一段來源摘要。"
body_en       = "The complete source description of this test rig."
body_zh       = "此測試平台的完整來源說明。"

[[item.section]]
heading_en = "Operating conditions"
heading_zh = "操作條件"
body_en    = "Add a section only when the source has this material."
body_zh    = "僅在來源包含這項資料時加入此段。"
items_en   = [
  "Maximum input: 3 kW",
  { type = "source-url", label_en = "Source:", label_zh = "來源：", value = "https://example.org/cold-plate-rig" },
]
items_zh   = [
  "最大輸入：3 kW",
  { type = "source-url", label_en = "Source:", label_zh = "來源：", value = "https://example.org/cold-plate-rig" },
]

[[item.figure]]
id         = "rig-diagram"
kind       = "diagram"
image      = "/assets/img/test-setups/example-cold-plate-rig/diagram.png"
w          = 1600                          # written by scripts/add-figure-sizes.py
h          = 904                           # never type these by hand
caption_en = ""                            # allowed only when the source gives no caption
caption_zh = ""
```

**Run `python scripts/add-figure-sizes.py` after adding any figure.** It reads the picture and
writes `w` and `h` into the row. The build needs them before it opens any file: they set the
shape of the row and they go on the `<img>` so nothing on the page jumps as the pictures arrive.
`python scripts/check-test-setup-import.py` fails if they stop matching the files.

### Then compose the page

The record has no layout in it. Each page lays itself out, in its own front matter, and the two
language files must say exactly the same thing:

```
+++
title    = "Example cold-plate test rig"
facility = "example-cold-plate-rig"
lang     = "en"
blocks = [
  "notes",
  "row:rig-photo rig-diagram",
  "row:flow-schematic",
]
+++

~~~
{{facility_page}}
~~~
```

Five kinds of block, and the order you write them is the order the page shows them:

| Block | What it puts on the page |
|---|---|
| `notes` | everything the record says: the lead paragraph and all its sections |
| `lead` | the lead paragraph on its own |
| `sec:2` | section 2 on its own, so its heading can sit right above the pictures it names |
| `row:a b c` | one row of pictures, by figure id |
| `split:a` | the words beside one picture, side by side on a laptop and stacked on a phone |

**A row lands every picture in it at the same height.** Widths come from each picture's shape, so
two pictures in a row fill the line with nothing cropped and no ragged bottom edge. Put pictures
that belong together in one row: a comparison set, a rig and its close-up, a photograph and the
drawing of the same thing.

**Rules the build enforces, so a mistake stops it rather than reaching the site:**

1. Every figure in the record appears in exactly one block. None dropped, none used twice.
2. The lead and every section are placed exactly once, by `notes` or by `lead` and `sec:n`.
3. A figure id that the record has not got is an error.
4. `python scripts/check-setup-pages.py` fails if the English and Chinese pages differ by
   anything other than their `lang` line.

**How to pick the rows.** Look at the pictures.

- One idea to a row.
- Two or four to a row reads best; three is fine when the three belong together.
- A wide schematic covered in small labels goes in a row of its own.
- Aim for a row about 340 to 480px tall for photographs, 250 to 340px for a set of micrographs.
- Overview first, then the system, then the parts, then the results.

`python scripts/shoot.py --emulate --sweep setup --widths 320,390,1440 --measure` renders every
detail page at three real widths and prints each row's heights, so a row that is not landing
level says so.

`[[item.section]]` and its structured `source-url` item are optional: use them only when the
source provides a section or a real `https://` source URL. Every figure belongs under the record
as `[[item.figure]]`; use `[[project.section]]` and `[[project.figure]]` for a project instead.
Put its images in `_assets/img/test-setups/<id>/` and use the matching `/assets/...` path in the
record. Empty captions are permitted only when the source supplies none.

Projects use the same `source_slides`, sections, and figures. An imported
project may omit `student` when the source does not identify a lab member. If you provide
`student`, it must exactly match an existing `id` in `_data/team.toml`; never infer or invent a
byline.

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
