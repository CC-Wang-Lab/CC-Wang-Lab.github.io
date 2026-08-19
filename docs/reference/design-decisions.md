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

The client owns `maysam-gholampour.github.io` and asked for the same feel. The scale is copied
exactly: **body 1.15rem / 1.5em, h1 weight 400, h2 and h3 italic at weight 400.** That
italic-roman pairing is the signature of ET Book, and it is deliberate.

Two exceptions. **Names stay roman**, because italic on a proper noun reads as emphasis rather than
style. And Chinese needs `Noto Serif TC` in the stack, because **ET Book has no CJK glyphs**.
Without it every Chinese page is a grid of empty boxes, and it looks perfect to anyone testing in
English.

---

## Why the colours are orange and blue

Sampled from the lab's own logo, already in use inside the CFD video: an **orange fish
(`#D89030`)** and a **blue fish (`#4080A8`)** curled into a cooling fan, on a dark navy ground
(`#181828`). Heat and cooling. The palette was chosen by whoever drew that logo. This site just
matches it.

**The mark in the navbar is a placeholder.** The original logo file, SVG preferred and otherwise
the largest PNG available, is still needed. The copy currently in the repo was pulled out of a
video frame at 220 by 130 pixels and is far too small for a favicon.

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
