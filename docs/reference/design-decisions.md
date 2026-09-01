# Design decisions, and why

Every choice made on 2026-08-19, with the reason under it. Written so that whoever changes one of
these in two years can see what it would cost.

---

## Who this site is for

**An engineering manager at a Taiwanese company who has never heard of this lab.**

*Why: the lab already has 29,400 citations and an h-index of 85. Academic credibility is not the
problem this website solves. What the site has to do is turn twenty active industrial
relationships into more of them, and recruit postdocs. Both audiences want the same thing first:
what can these people actually do.*

The rule that follows: **the site is the front door of a 60-person R&D organisation, not a larger
version of a professor's personal page.**

---

## The eight architecture decisions

| Decision | Chosen | Reason |
|---|---|---|
| Repository | `CC-Wang-Lab.github.io` | A user site serves at the root. No `prepath`, so no broken-CSS trap. A custom domain can be added later with one `CNAME` file. |
| Languages | English **and** 繁體中文 | Local companies and students read Chinese. International partners and journals read English. |
| CSS framework | **Bootstrap 5.3 via CDN** | Tailwind needs a Node build step inside the Action, and Franklin generates the HTML *after* Tailwind would need to scan it. Bootstrap is one link tag and already ships `data-bs-theme` light/dark. |
| Navigation | 6 links + 1 CTA button | See below. |
| Client logos | **None at launch** | See below. |
| Publications | ~40 selected by theme + Scholar link | All 578 is a wall nobody reads, and the full record already exists on Scholar and the NYCU hub. |
| Team | Placeholder cards + a TOML data file | Sixty photos and bios cannot be collected before anyone has seen the design. |
| Hero | Captioned pool-boiling footage | See below. |

---

## Why there is no client logo wall

The original plan had an "Our Clients" section. It was removed.

*Why: most of the lab's industrial work is under NDA, and no company has been asked for permission
yet. An empty logo wall does not communicate confidentiality. It communicates "perhaps they do not
have clients". That is the single worst thing this page could say about a lab running twenty
concurrent industrial projects.*

What replaced it: an **Industrial R&D at scale** band with four sector cards and one honest line:
*Many industrial collaborations are confidential. Organisations are named publicly only where
disclosure has been approved.*

**When six or more written permissions have arrived**, add a restrained "Selected collaborators"
row inside the Industry page. Not on the home page, and not called "Our Clients" — "clients" makes
a university laboratory sound like a consultancy.

**On testimonials:** company quotes are rare and slow, because legal and PR must approve every
word. **Alumni quotes** are the workable substitute. A former lab member now at a thermal company
has no NDA to clear and is usually pleased to be asked.

---

## Why "Capabilities" and not "Facilities"

*Why: "Facilities" makes an academic think "show me your equipment". An industrial engineer is
asking a different question. Can you test my cold plate, can you measure boiling on my surface,
can you validate my airflow before I build it. Equipment is the evidence underneath the answer,
not the answer.*

The same reasoning turned "Work with us" into **"Discuss an R&D project"**. "Work with us" can mean
apply for a PhD, apply for a postdoc, hire us, or sponsor research. The visitor should not have to
click to find out which.

---

## Why the numbers band says what it says

```
50-60 researchers  |  20+ active industry projects  |  12 patents  |  29,400 citations
```

Four numbers, four different stories: **scale, industrial demand, technology output, academic
authority.** Four bibliometric numbers would have told one story four times.

**"578 papers" was in the first draft and is wrong.** 578 is research *outputs* — 439 journal
articles, 59 conference contributions, 31 conference articles, 16 reviews, 12 patents. Calling
that "papers" is exactly the small error a technical reader spots and remembers. The h-index of 85
moved off the home page. To a company engineer, **21 years of industrial R&D at ITRI** is the more
persuasive fact, and it now leads the credibility block.

---

## Why the hero is boiling footage, and why it is captioned

Three sources were available: a CFD animation of a CPU cooler, a building visualisation, and
high-speed pool-boiling footage (R1233zd, 65% porosity porous surface, 2.5 bar).

**The boiling won.** It is real experimental footage with no user interface in the frame, it is
nearly black so white text sits on it cleanly, and bubbles are inherently watchable. The CFD clips
are screen recordings of a Makie application window — title bar, sliders, gauges — and even
cropped they read as somebody's desktop.

**It is captioned** because unlabelled bubbles are just bubbles. A visitor who cannot tell what
they are looking at gets decoration instead of evidence.

Measured, not estimated:

| File | Size |
|---|---|
| Source | 23.0 MB |
| Hero, 1280 px, 10 s, CRF 36 | **996 KB** |
| Same clip as WebM VP9 | *larger* — dropped |

---

## Why the type looks like this

The client owns `maysam-gholampour.github.io` and asked for the same feel. The **proportions** are
copied: h1 weight 400, h2 and h3 italic at weight 400. That italic-roman pairing is the signature
of ET Book, and it is deliberate.

Two exceptions. **Names stay roman**, because italic on a proper noun reads as emphasis rather than
style. And Chinese needs `Noto Serif TC` in the stack, because **ET Book has no CJK glyphs**.
Without it every Chinese page is a grid of empty boxes, and it looks perfect to anyone testing in
English.

### The ladder, added 2026-08-19 and refined 2026-08-29

The first version had **74 `font-size` declarations across 33 different values**, the smallest at
0.62rem = 9.9 px. Fourteen of those values sat inside a 4.5 px band, which the eye reads as noise
rather than as hierarchy. They are now nine tokens.

| token | 375 px | 1440 px | used for |
|---|---|---|---|
| `--fs-4xl` | 35.2 | **57.6** | the hero title, Narrative profile name |
| `--fs-3xl` | 35.2 | **48.8** | h1, Editorial profile name |
| `--fs-2xl` | 25.6 | **37.6** | h2, Dossier profile name |
| `--fs-xl` | 20.8 | **28.0** | h3, card-level h2 |
| `--fs-lg` | 19.2 | **22.4** | h4, card titles, leads |
| `--fs-md` | 17.6 | **19.2** | body |
| `--fs-sm` | 16.0 | **17.6** | secondary prose, controls, form fields, profile/project chips |
| `--fs-xs` | 14.4 | **15.2** | functional labels, dates, captions, table/footer headings |
| `--fs-2xs` | 12.8 | 12.8 | decorative metadata and eyebrows. **A hard floor.** |

*Why the lower ladder changed: ET Book's body and supporting text were visually slight beside the
unchanged headings, particularly on wide screens. Body now grows from 17.6 to 19.2 px; supporting
text grows from 16 to 17.6 px; and functional labels grow from 14.4 to 15.2 px. The 12.8 px token is
reserved for decorative metadata. Every `clamp()` is solved to hit its minimum at 375 px and its
maximum at 1440 px, while the established `--fs-lg` through `--fs-4xl` endpoints stay untouched.*

*Why the ladder grows at the top and not at the bottom: the heading-to-body ratio used to run the
wrong way. `body` dropped to 1.05rem below 768 px while `h1`–`h5` never changed, so a phone got the
most dramatic headings and a monitor the least. With the revised reading scale it is now 2.00 at
375 px and 2.54 at 1440 px.*

**`--fs-sm` is 16 px and must not go lower.** Below 16 px, iOS Safari zooms the page when a form
field takes focus.

**`line-height` is unitless everywhere.** `body { line-height: 1.5em }` computed once to a fixed
27.6 px and every descendant inherited that absolute length whatever its own size, so a 10.9 px
badge carried 27.6 px of leading.

**The hero title uses a balanced text rail, not manual line breaks or full justification.** Its
20ch English measure (18em for CJK) remains active at every viewport width, and `text-wrap: balance`
chooses the line endings. Future headline changes therefore reflow without sentence-specific CSS;
natural word spacing is preserved and the typed line and actions keep the same left axis.

**`--font-ui` no longer starts with `Noto Serif TC`.** That face ships a Latin subset
(`unicode-range: U+0000-00FF`), so all 32 rules that asked for the "UI" font were rendering English
in a Chinese serif and never reached Segoe UI. The site is now one family on purpose, matching
`maysam-gholampour.github.io`, which uses ET Book on every element.

**ET Book ships exactly two weights**, 400 and 700, plus a 400 italic. There is no 500 and no 600,
so `font-weight: 500` rendered as 400 and `600` rendered as 700. The navbar asked for 500, which
did nothing at all. Only 400 and 700 are written now.

---

## Why profiles use the header identity design, added 2026-08-29, revised 2026-08-30

The former D option is the selected and sole public profile design. Each profile generates its
portrait, role, topic and links from one team record and places them in the page header. The body
contains only the narrative and academic record, so there is no hidden duplicate identity block.
English and Traditional Chinese therefore continue to share the same data relationships.

The profile name uses `--fs-3xl`, narrative copy `--fs-md`, narrative headings `--fs-xl`, fact
values `--fs-sm`, and fact labels `--fs-xs`. The portrait is capped at 180px on wide screens. The
role and unlabelled, pipe-separated expertise sit in one row beneath the name, followed by one row
of contact controls; the portrait remains at the right. The usual short title rule is omitted so
the two identity rows form the name's visual anchor. These rows wrap safely before the header
stacks on narrow screens. ET Book, Noto Serif TC, the color system and the 44px control minimum
remain unchanged.

The old `profile-layout` query, A/B/C/D switcher, comparison pages and conditional layout styles
are no longer published. Existing URLs that retain the obsolete query still resolve to the normal
profile because the server ignores query parameters. The archived alternatives and their recovery
commits are recorded in `docs/archive/profile-layout-variants.md`.

Page-header notes, section introductions and prose notes now follow the full width available in
their content container instead of a separate 74ch cap. They remain justified at every viewport,
including phones; headings and functional labels stay left-aligned.

---

## Why the colours are orange and blue

Sampled from the lab's own logo, already in use inside the CFD video: an **orange fish
(`#D89030`)** and a **blue fish (`#4080A8`)** curled into a cooling fan, on a dark navy ground
(`#181828`). Heat and cooling. The palette was chosen by whoever drew that logo. This site just
matches it.

**The mark in the navbar is a placeholder.** The original logo file, SVG preferred and otherwise
the largest PNG available, is still needed. The copy currently in the repo was pulled out of a
video frame at 220 by 130 pixels and is far too small for a favicon.

### A logo colour is not a text colour, added 2026-08-19

The three brand hexes are unchanged and still fill every button and band. What changed is that
**they stopped carrying text in light mode**, because they cannot.

```
#d89030 on the light page  =  2.58 : 1
#eda43f on the light page  =  2.05 : 1     <- the old link HOVER
#4080a8 on the light page  =  4.20 : 1
                    AA needs 4.5 for body text, 3.0 for a control border
```

Twenty-one rules used a brand hex as text. Eleven of them failed. The worst two were the link
hover, where **hovering a link made it harder to read than not hovering it**, and the dark theme,
where `--lab-accent` and `a:hover` both resolved to `#eda43f`, so **hover changed nothing at all**.

Three derived tokens now carry text, and each flips with the theme:

| token | light | ratio | dark | ratio |
|---|---|---|---|---|
| `--lab-accent` | `#9c6014` | 5.00 | `#eda43f` | 8.69 |
| `--lab-accent-hover` | `#7a4f0e` | 6.94 | `#f7c579` | 11.51 |
| `--lab-accent-2` | `#2d5c7a` | 7.01 | `#5aa0cc` | 6.39 |
| `--lab-border-strong` | `#948d7e` | 3.30 | `#6a6a85` | 3.21 |
| `--lab-danger` | `#a5160f` | 7.53 | `#f2b8b5` | 10.71 |

*Because they flip by themselves, four `[data-bs-theme="dark"] .x` patch rules that existed only to
swap blue for blue-bright are gone. The change deletes more than it adds.*

`--bs-border-color` stays as it was. It is the **decorative** hairline at 1.35:1, which is right for
a rule between sections and wrong for the edge of a form field. Controls use `--lab-border-strong`.

The always-dark regions — hero, CTA band, news slider, motion toggle — used **15 white-alpha
literals across 10 different alphas**. They are three tokens now: `--on-dark-1/2/3` at 0.92, 0.78
and 0.60, whose worst case over the four grounds those regions actually use is 9.41, 7.29 and 5.03.

**`scripts/check-contrast.py` asserts every pair above.** Run it after any colour change.

---

## Why every stylesheet and script URL ends in `?v=<hash>`

**The symptom.** The site was deployed and visitors still saw the old page until they pressed
Ctrl+F5. Some saw something worse: the new markup wearing the old stylesheet.

**The cause**, read off the live site on 2026-08-20:

```
$ curl -sSI https://cc-wang-lab.github.io/css/style.css
Cache-Control: max-age=600
```

GitHub Pages sends that on every file it serves. Ten minutes, and it cannot be changed. Pages
reads no `_headers` file, no `.htaccess`, and has no per-file setting.

Ten minutes on the HTML alone would be harmless. The damage came from the HTML and the stylesheet
expiring **on separate clocks**. A visitor could hold a fresh `index.html` and a stale `style.css`
at the same time. That page is not old. It is broken.

**The fix.** The build puts each file's own content hash in its URL.

| | |
|---|---|
| The file changed | The URL changed, so the browser must fetch it |
| The file did not change | The URL is identical, so the cache still works |

`fingerprint()` in `utils.jl` does it, using the first 8 hex digits of the file's SHA-1. Twelve
URLs, on all 30 pages. Fonts, icons and the hero video are left alone on purpose: those change by
being replaced with a differently named file, which busts itself.

**What this does not fix, and cannot.** The HTML page is still held for up to ten minutes, and
nothing on GitHub Pages can shorten that. The ten minutes are now bounded and harmless. A visitor
gets the whole old page or the whole new page, never a mix, and it heals itself.
**Nobody has to hard reload, and nobody has to be told to.**

Motion state follows the same expectation. Every new page starts moving; the shared Play/Pause
control changes only the current page. An obsolete saved `labMotion=off` value is ignored, so a
normal reload never requires storage cleanup to restore the hero, news slider, or partner rows.

If ten minutes ever becomes too long, the answer is a CDN in front of Pages, or a host that reads
a `_headers` file. That is a hosting change, not a code change.

### The trap underneath it

Franklin tokenizes `<script ` as the opening of a block it must not touch, and copies everything up
to `</script>` out verbatim. So this **ships broken and says nothing**:

```html
<script src="{{asset /assets/js/motion.js}}"></script>
```

The `{{...}}` reaches the live site as literal text and the script never loads. A `<link>` has no
such problem, which is why the stylesheet worked on the first try and eleven script tags did not.

`{{scripts motion theme-toggle reveal}}` writes the whole tag from outside the script element.
That is why the script list in `_layout/foot.html` is a list of names and not eleven lines of HTML.
**The order of the names is the load order.**

The build gate in `.github/workflows/Deploy.yml` greps `__site` for any surviving `{{...}}` and
fails the run. It caught this one on the first build. Its character class was widened to include
`.` and `-` so that it can see a path.

---

## Why the detail-page figures are placed by space and not by name, 2026-08-31

> **Superseded the same day by the section below.** Layouts `a`, `b` and `c` are gone and each
> page composes itself. The fault this section records is the reason, so it stays.

The 26 imported facility and project pages each pick a layout, `a`, `b` or `c`. The layout chose
where the notes sat. The figures inside it were placed by rules naming four literal figure ids:
`cabinet`, `dimensions`, `100w` and `500w`.

**One record in the site carries those ids.** `falling-film-cooling-system`, and it is layout
`c`. So the entire layout-`b` ruleset matched nothing at all, and 25 of the 26 records fell
through to auto-placement in a track built for a different record. Every gate passed the whole
time, because no gate could see it.

Measured at 1440 px before the change:

| Symptom | Records affected |
|---|---|
| 1 to 3 figures in a 4-column track, 25% to 75% of the row empty | **8** (every layout `b`) |
| Narrow and wide columns alternating by source order | **7** (every other layout `c`) |
| Four micrographs of one comparison set at two different sizes | `boiler-surface-test-rig` |
| Each photo 136 px wide at a 320 px screen | every multi-figure record |

The whole of it is now one rule with no figure id in it:

```css
grid-template-columns: repeat(auto-fit, minmax(min(100%, var(--fig-min)), 1fr));
```

`auto-fit` collapses tracks nothing lands in, so an empty cell in a full row cannot happen.
The floor decides the column count from the room available, so a 320 px screen gets exactly one
column. A record added tomorrow needs no CSS.

**Emphasis moved into the data**, as `span = "full"` on a `[[figure]]` row. It has to live there:
CSS knows how many figures there are and how much room it has, and it cannot know that one of
them is a wide schematic whose labels are unreadable at a quarter width. A person looking at the
picture knows that. Ten figures across nine records carry it.

*Rejected: keying emphasis off `kind = "diagram"`, which is what the old rule did. Five of the
six figures on `boiler-surface-test-rig` are diagrams, so it stacked four micrographs full width
in four near-empty boxes.*

*Rejected: `span 2`. On a phone the track is one column, and a two-column span there creates an
implicit second column and pushes the page wider than the screen. `1 / -1` is safe at any track
count.*

## Why the notes on a detail page have no width cap, 2026-08-31

> **Reversed the same day.** The notes carry a measure again, and it is measured this time:
> `58ch`. The reason it was removed and the reason it came back are different, and both are
> below.

`.setup-study-copy` carried `max-width: var(--measure)`, the site's 74ch reading measure. It was
the only note block on the site that did, and `scripts/shoot.py --measure` fails any other note
that carries a second cap.

In layouts `a` and `c` the copy already sits in a grid column narrower than 74ch, so the cap
could never bind. In layout `b` the copy **is** the container, so the cap was the only thing
acting, and what it did was hold the notes to 700 px inside a 1320 px row and leave the right
half of the page empty. On all eight layout-`b` records.

The cap is gone. `check-setup-renderer.py` now asserts its absence, and asserts
`overflow-wrap: break-word` alongside it.

## The reading measure, measured at last, 2026-08-31

`style.css` names **45 characters** as the floor below which justified text opens rivers. Nothing
had ever measured against it, because the screenshot harness could not render below 492 px.

Characters per line, counted as box width over the average character width of the element's own
text in its own computed font:

| Width | Characters per justified line | Under the floor |
|---|---|---|
| 320 px | 36 – 43 | **every page** |
| 360 px | 41 – 49 | 6 pages |
| **390 px** | **45 – 53** | none |
| 768 px | 84 – 92 | none |
| 1440 px | 51 – 92 | none |

**Justification stays on at every width**, by the site owner's decision on 2026-08-31. The number
is recorded here so the decision has its evidence attached, and so that anyone who revisits it
starts from a measurement instead of an impression.

*The first version of this measurement was wrong and reported 20 to 30 characters. It counted
text length over line count, which undercounts twice: an inline `<strong>` sits a fraction of a
pixel off its line and a rounded top invented an extra line, and the last line of a paragraph is
short so it drags the average down. Both push the number the same way, so the check was reporting
rivers that were not there.*

## Why each detail page composes itself, 2026-08-31

The section above replaced figure ids in the stylesheet with an auto-fit track. That fixed what a
generic grid can fix, and it went as far as a generic grid can go. **What was left could not be
fixed by any stylesheet, because the thing that decides the layout is what the pictures ARE.**

One record is four micrographs of one comparison set. The next is a rack photograph beside a dot
grid 497 px wide and 1600 px tall. No rule can tell those apart, and no third layout letter would
have helped: the site would have had `d` and `e` and the same problem.

So the record keeps the words and the pictures, and **the page keeps the layout**:

```
blocks = [
  "row:test-rig",
  "row:test-schematic",
  "notes",
  "row:sintered additively-manufactured",
  "row:diamond acid-etched",
]
```

### The arithmetic, because it is the whole idea

Each figure is a flex item with `flex: aspect 1 0`. A zero basis means the free space is shared
out in proportion to `flex-grow`, so

```
width_i  = (W - gaps) x a_i / sum(a)
height_i = width_i / a_i = (W - gaps) / sum(a)
```

and the second line has no `i` in it. **Every picture in a row lands at exactly the same height**,
whatever shapes are in it, filling the line with nothing cropped and no ragged bottom edge. It is
the Flickr justified gallery with no JavaScript and no measuring pass.

Measured across all 26 pages at 1440 px: **every row's height spread is 0.00 px.**

### The cap goes on the row, never on the image

A picture must never be painted wider than its own pixels. Slot width is `a_i x h`, so the
no-upscale condition `a_i x h <= w_i` reduces to `h <= h_i`, and the largest safe row height is
the smallest natural height in the row. The renderer emits that as `--nat-h` and the stylesheet
applies it to the row's `max-width`, because `h = (W - gaps) / sum(a)` means capping the height
IS capping the width.

*Rejected: `max-height` on the `<img>`. It looks like the same thing and is not. It shrinks the
picture inside a slot that is still the old width, so the row goes ragged again and gains a
letterbox.*

The ceiling above that is **`--fig-max-h: 40rem`**. 32rem was tried first and was too tight: it
held the row of four tall rack pictures on `data-center-air-cooling-facility` to 891 px inside a
1320 px container, so a third of the line sat empty.

### Why the composition is front matter and not `{{figrow a b}}` in the body

The approved plan said row calls in the page body. **An unknown hfun name does not throw.**
Franklin logs a warning and substitutes an empty string, so `{{figrpw a b}}` builds green with two
pictures missing and no `{{ }}` left in the HTML for CI to grep.

That is the same silent-no-op that put 25 of 26 records into the wrong grid, and it is the fault
this whole pass exists to remove. A front-matter list cannot misspell a function name, because
there is no function name in it, and every id in it is checked at build time.

**What the build refuses to compile**, each of them a mistake somebody can make while composing:

| Refused | Because |
|---|---|
| a figure named in no block | it would silently vanish from the page |
| a figure named twice | the same picture twice, in two sizes |
| an id the record has not got | a typo in a figure id |
| a section placed twice, or not at all | a heading lost, or repeated |
| a lead on a record that has none | an empty `<p>` and a gap nobody can explain |

`scripts/check-setup-pages.py` adds the one thing the build cannot see: **the English and Chinese
pages must differ by exactly one line, the `lang` line**. It runs in CI, blocking. A composition
applied to one language only is the failure this architecture exists to prevent.

### `span = "full"` is retired with the layouts

It said "give this figure the whole track" in a grid where the alternative was a quarter of one.
A row already gives every figure a share proportional to its shape, and a row of one is the
composer's way of saying this picture gets the width. Two mechanisms for one thing is how the
last fault survived four gates.

### The measure, reversed and then measured

`58ch`, not the `72ch` that was tried first and not the `74ch` used elsewhere. **`ch` is the width
of a zero**, and ET Book's zero is 9.39 px where its average character is 7.90 px, so a 72ch box
held 85 to 90 characters a line across the 26 records. 58ch measures **60.7 to 72.3**, which is
the band this is aiming at.

The cap itself came back for a reason the earlier decision could not have known: under layout `b`
the notes WERE the container, so a cap left the right half of the row empty. Under rows nothing
sits beside the notes, so there is no half to leave empty, and without a cap the line runs to
about 160 characters.

### Every picture links to its own file

Ten of these figures are apparatus schematics with twenty to thirty labels drawn into the pixels.
At 320 px they are an overview and nothing else, and no layout changes that: the label text is
8 px tall in the source.

So `.fig-media` is an `<a>` to the image file. The phone's own viewer pinch-zooms and pans it, and
the page gains no JavaScript, no lightbox and no second copy of the picture. A corner mark appears
on hover where there is a pointer, and is always visible on a touch screen, which has no hover to
discover it with.

### What the harness checks now

`shoot.py --measure` had **no upscale check at all**, and its three setup probes selected
`.setup-study-figure`, which no longer exists: they reported "clean" while finding zero images on
all 52 pages. They are replaced by one row audit that fails on the two properties the whole
architecture rests on — a height spread over 1 px, and any picture painted above its natural
width.

### The composition rules, applied by eye to all 26

Checked against an outside review before any page was composed:

1. One idea to a row.
2. Give every picture its minimum readable width before worrying about filling the line.
3. A dense schematic or an extreme panorama goes in a row of its own.
4. Keep a comparison set together, equally weighted, in its own order.
5. Two or four to a row reads best; three is fine when the three belong together.
6. Never let a narrow screen invent a full-width orphan. A row of three or more becomes two even
   columns below 992 px and one below 576 px; it never re-justifies on a second line, because
   wrapping and justifying are the same mechanism fighting.
7. Photographs want a row 340 to 480 px tall, micrograph sets 250 to 340 px. Judge a schematic by
   width instead.
8. Keep the prose near 60 to 75 characters a line even above a full-width figure.
9. Mix captioned and uncaptioned pictures in one row only when they clearly belong together.
10. Order the page from orientation to inspection: overview, system, parts, then results.

**Side by side needs a landscape hero.** `split:` puts the words beside one picture, and it was
used on four records and then cut to three. On `thermal-fin-natural-convection-chamber` the hero
is a portrait: the photograph came out 360 px inside a 733 px column with the text ending 174 px
before it began. A portrait hero gets the words above it instead.

## Why the screenshot harness drives a debug port, 2026-08-31

`scripts/shoot.py` says never to pass `--remote-debugging-port`, because that is the flag that
makes a Chromium binary attach to an instance already running. `scripts/cdp.py` passes it anyway,
and the warning is still true.

Chromium decides "am I already running?" from a lock inside `--user-data-dir`, not from the port.
Every launch here gets a throwaway profile named after the process id, so there is no instance to
attach to and a real browser always starts. The port is 0, so the OS picks a free one.

**What it buys is the only honest phone width this project has ever had.** Headless Edge on
Windows will not open a window narrower than about 508 DIP: ask for 320 and it lays the page out
at 484 and crops the screenshot to 320. The picture looks like a phone and is a lie.
`Emulation.setDeviceMetricsOverride` sets the layout viewport instead, so 320 is 320, and the
harness asserts `window.innerWidth` matches before it will write a file.

That assertion found a defect on its first run. `amca-wind-tunnel` could not fit 320 px, because
`TUNNEL+Environmental` in its title has no break opportunity; the browser widened the viewport to
402 px to fit it and the menu button fell off the screen.

## Three bugs from the source site that were not copied

The client's own site carries these. They are fixed here, and each fix is commented in place.

1. `nav.html` had `onclick="toggleDarkMode()"` calling a function that exists nowhere. A silent
   `ReferenceError` fired on every click.
2. The icon-swap code in the theme script was commented out, so the sun and the moon both showed
   at the same time.
3. The anti-flash script hardcoded `"dark"` and ignored `prefers-color-scheme`, so a visitor whose
   laptop was set to light mode still got a dark page.

---

## What is deliberately not here yet

A members-only area, real team photos and bios, approved client logos, the full 578-item
publication list, RSS, site search, a custom domain, and analytics.

**One gap worth naming.** The twenty publications in `publications.toml` are the *most-cited* ones,
which skews old and skews towards fin-and-tube heat exchangers. The site sells electronics cooling
and data centres, and almost nothing from that work is on the page, because those papers are recent
and have not accumulated citations yet. **Add 15 to 20 papers from 2022–2026 under the
`electronics` and `two-phase` themes before launch.** Recency matters more than citation count to
an industrial reader.
