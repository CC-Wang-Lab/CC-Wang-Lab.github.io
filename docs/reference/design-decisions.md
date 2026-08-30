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

**`--font-ui` no longer starts with `Noto Serif TC`.** That face ships a Latin subset
(`unicode-range: U+0000-00FF`), so all 32 rules that asked for the "UI" font were rendering English
in a Chinese serif and never reached Segoe UI. The site is now one family on purpose, matching
`maysam-gholampour.github.io`, which uses ET Book on every element.

**ET Book ships exactly two weights**, 400 and 700, plus a 400 italic. There is no 500 and no 600,
so `font-weight: 500` rendered as 400 and `600` rendered as 700. The navbar asked for 500, which
did nothing at all. Only 400 and 700 are written now.

---

## Why the four profile designs share one record, added 2026-08-29, revised 2026-08-30

Editorial, Dossier, Narrative-first and Header profile are design choices, not four versions of a
person's record. Every identity presentation is generated from the same team row. Modes A-C show
the ordinary body identity; mode D hides that presentation and shows the same portrait, role,
topic and links inside the page header. A wording or factual correction is consequently made once
and remains identical in every option, both in English and Traditional Chinese.

The allowlisted query parameter is `profile-layout=editorial|dossier|narrative|header`. Missing,
empty or invalid values resolve to Editorial before first paint. The A/B/C/D switcher appears on
every real profile, updates the URL with `history.replaceState`, and writes nothing to local or
session storage.

The four layouts use the existing typography ladder rather than new sizes: Editorial names use
`--fs-3xl`, Dossier names `--fs-2xl`, Narrative-first names `--fs-4xl`, roles `--fs-lg`, narrative
copy `--fs-md`, narrative headings `--fs-xl`, fact values `--fs-sm`, and fact labels `--fs-xs`.
Header profile uses a `--fs-3xl` name and caps its portrait at 180px on wide screens. Its role and
pipe-separated expertise sit in one row beneath the name, followed by one row of contact controls;
the portrait remains at the right. The usual short title rule is omitted in this mode so the two
identity rows form the name's visual anchor. These rows wrap safely before the header stacks on
narrow screens. ET Book, Noto Serif TC, the color system and the 44px control minimum remain
unchanged.

Page-header notes, section introductions and prose notes now follow the full width available in
their content container instead of a separate 74ch cap. They remain justified at every viewport,
including phones; headings and functional labels stay left-aligned.

The unlinked `/profile-designs/` and `/zh/profile-designs/` pages are marked `noindex` and exist
only for selection. After one design is approved, those pages, the switcher and unused CSS states
can be removed without migrating or reconciling profile content.

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
