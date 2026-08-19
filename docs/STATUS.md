# Where this project stands

Written 2026-08-19, after round 4. Read this first when picking the work back up.

## What exists

Bilingual website for **Prof. Chi-Chuan Wang (王啟川)**, Chair Professor of Mechanical Engineering
at NYCU. Franklin.jl, Bootstrap 5.3, no build step.

| | |
|---|---|
| Repo | `c:\Dev\_Projects\34-CC-Wang-Lab-Website\CC-Wang-Lab.github.io` |
| Commits | 13, working tree clean |
| Pages | 24 — 12 per language |
| Size | 5.4 MB |
| Target | `https://cc-wang-lab.github.io/` — a **user site**, so **no `prepath`** |

```bash
julia --project=. -e 'using Franklin; serve()'      # http://localhost:8000
julia --project=. -e 'using Pkg; Pkg.instantiate()' # once per machine
```

**Navigation:** Home · Projects · People · Publications · News, plus a
**Project inquiries** button, a 中文 switch and a dark/light toggle.
About and Contact are reached from the footer.

**Home page:** hero video with a typed line → news slider → research cards → partners strip →
Prof. Wang → call to action.

## The one idea the whole site rests on

**Every list is generated from `_data/*.toml` at build time. Nobody writes HTML.**

| File | Generator | Appears on |
|---|---|---|
| `ui.toml` | `hfun_ui` | every interface string, both languages |
| `team.toml` | `hfun_people_pi/_leads/_postdocs/_phd/_msc/_alumni` | People, Alumni, Home |
| `projects.toml` | `hfun_project_grid`, `_header`, `_featured` | Projects and each project page |
| `research.toml` | `hfun_research_cards` | Home |
| `partners.toml` | `hfun_partner_strip` | Home |
| `publications.toml` | `hfun_publications` | Publications |
| `news.toml` | `hfun_news`, `hfun_news_slider` | Home, News |
| `capabilities.toml`, `sectors.toml` | `hfun_capabilities`, `hfun_sectors` | About |

Two cross-references are enforced at build time: a project names its **researcher** by an id in
`team.toml` and its **research area** by an id in `research.toml`. A wrong id **stops the build**
with a message naming it. That guard has already caught two real renames.

## Blocked, waiting on Maysam

1. **Push access to `CC-Wang-Lab`.** `gh` is authenticated as `maysam-gholampour`; that account has
   0 repos. Nothing has ever been pushed.
2. **The client-logo collage file.** Asked for three times. It was pasted into chat and is not on
   disk — I searched every image over 80 KB. It holds all 44 missing logos in one picture.
3. **The NDA check.** Prof. Wang approved publishing all ~80 organisations. His office should still
   confirm none are under an agreement forbidding disclosure — that is contract risk, and no
   trademark argument fixes it.

## Placeholder content still on the site

| Where | State |
|---|---|
| `team.toml` | Only Prof. Wang and Maysam are real. Everyone else is a placeholder. |
| `news.toml` | All three items say PLACEHOLDER, and they sit directly under the hero. |
| `partners.toml` | 15 of 59 have a logo; the other 44 are in `_assets/img/partners/NEEDED.md`. 18 names are marked uncertain — read off a small image. |
| `publications.toml` | 20 real papers, but they are the *most-cited*, so they skew old and skew to fin-and-tube. **Add 15–20 recent (2022–2026) electronics-cooling and two-phase papers**; that is what the site sells. |
| Research area images | 4 of 6 say "image to be supplied". |
| Team photos | All the grey silhouette. |
| Chinese | Written by Claude. **Needs a native Traditional Chinese review** before launch. |
| Content licence | Not chosen. The lab's own text and images have no stated terms. |

## Traps already paid for — do not rediscover these

| Trap | What happens |
|---|---|
| **The motion flag persists** | `localStorage.labMotion` survives reloads. A test that pauses motion leaves the reviewer's browser paused, and the strip gets reported as broken. **Clear it at the end of every motion test.** |
| **Chrome bursts animation frames** | In an unfocused window, 12 frames fired over 7590 ms with only 892 ms *between* them. Anything adding `speed × dt` per frame crawls. `partners.js` computes position from **absolute elapsed time** instead. |
| **Scrollbar shifts the layout** | A page short enough to need no scrollbar is 20 px wider, so its centred container sits 10 px right. `scrollbar-gutter: stable` on `html` is the fix. |
| **Logo search returns the wrong logo** | "ASE Group" returned the European Space Agency banner, "Lite-On" an unrelated "TL" mark, "Google" the 2012 Google Play logo. **Look at every file before accepting it.** |
| **Heredocs break in this shell** | `cat <<'EOF'` fails on apostrophes in the content. Use Python or the Write tool for prose files. |
| **`prefers-reduced-motion` is not consulted** | Deliberate, and argued out in `.claude/rules/animation.md`. Motion starts for everyone and a visible control stops it. Do not put the old behaviour back without reading that file. |
| **One section per research area reads as a column** | With six areas and three projects, every section held one card, so the grid never got to put two side by side. `/projects/` is now ONE grid with an area filter bar; `project-filter.js` reads `#<area-id>` from the URL so the home-page research cards still land on the right filter. Put sections back only once each area has several projects. |

## Where the reasoning is written down

- `.claude/rules/` — animation, bilingual, data files, media, serve
- `docs/architecture.md` — five Mermaid diagrams
- `docs/how-to-edit.md` — written for lab members, not developers
- `docs/reference/design-decisions.md` — every choice with its reason
- `docs/reference/chatgpt-round1.md`, `wording-round1.md`, `wording-typed.md` — outside critique,
  saved verbatim. **These are records. Do not edit them**, including their British spellings.
- `_assets/img/partners/SOURCES.md` — where each logo came from and its copyright status

## The next three things worth doing

1. **Replace the three placeholder news items.** They are the most visible fake text on the site,
   sitting directly under the video.
2. **Get the collage file** and finish the remaining 44 logos.
3. **Add the recent publications.** The current list undersells exactly the work the site is built
   to sell.
