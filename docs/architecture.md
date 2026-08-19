# Architecture

Four diagrams. Update them in the **same commit** as the change that makes one stale.

## Rules

Every rule that governs this repository. Blue is global, green is local, red is the one that must
never be broken.

```mermaid
mindmap
  root((CC Wang Lab site))
    Global
      Plain English
        Answer first
        Numbers in tables
        No paired dashes
      Verify before claiming
      Scope discipline
      Branch discipline
        Never switch without asking
        Merge with --no-ff
      Commits
        No AI attribution
      Golden files
        Never regenerate
      Shell
        Bash and Unix syntax first
    Local
      franklin-serve.md
        Run from repo root
        clear=true after utils.jl
      bilingual.md
        Mirrored zh/ folder
        Always use url and ui
        CJK font or empty boxes
      data-files.md
        NEVER hand-write a list
        last_verified staleness check
      media.md
        Hero under 1 MB
        muted or autoplay dies
        No WebM on this footage
```

## Branching

`main` is the only long-lived branch. The Action publishes to `gh-pages`, which is generated and
never edited by hand.

```mermaid
%%{init: {'gitGraph': {'mainBranchName': 'main'}} }%%
gitGraph
  commit id: "first draft"
  branch content/team
  commit id: "real photos and bios"
  checkout main
  merge content/team
  branch content/zh-review
  commit id: "native Chinese review"
  checkout main
  merge content/zh-review
  commit id: "logo file added" type: HIGHLIGHT
```

## How a page is built

Data goes in on the left, HTML comes out on the right. **No list on this site is written by hand.**
The dashed arrows are the cross-references: a project names its researcher and its research area by
id, so neither is ever typed twice.

```mermaid
flowchart LR
  subgraph edit["Edited by lab members"]
    UI["_data/ui.toml<br/>every interface string"]
    D1["_data/team.toml"]
    D2["_data/research.toml"]
    D7["_data/projects.toml"]
    D3["_data/capabilities.toml"]
    D4["_data/sectors.toml"]
    D5["_data/publications.toml"]
    D6["_data/news.toml"]
  end

  subgraph src["Page sources"]
    EN["*.md and projects/*.md<br/>lang = en"]
    ZH["zh/*.md and zh/projects/*.md<br/>lang = zh"]
  end

  UTILS["utils.jl<br/>hfun_* generators<br/>pick() picks _en or _zh<br/>{{url}} adds the /zh prefix"]
  LAY["_layout/"]
  CSS["_css/style.css"]
  JS["_assets/js/<br/>theme, hero video, news slider"]
  ASSET["_assets/<br/>video, fonts, images"]

  D7 -.->|student id| D1
  D7 -.->|area id| D2

  UI --> UTILS
  D1 --> UTILS
  D2 --> UTILS
  D7 --> UTILS
  D3 --> UTILS
  D4 --> UTILS
  D5 --> UTILS
  D6 --> UTILS

  EN --> FR["Franklin.jl"]
  ZH --> FR
  UTILS --> FR
  LAY --> FR
  CSS --> FR
  JS --> FR
  ASSET --> FR

  FR --> SITE["__site/<br/>26 pages, 2 languages"]
  SITE --> GHA["GitHub Action<br/>optimize + brace check"]
  GHA --> PAGES[("gh-pages branch<br/>cc-wang-lab.github.io")]

  classDef arch fill:#8250DF,stroke:#8250DF,color:#fff
  classDef crit fill:#CF222E,stroke:#CF222E,color:#fff
  classDef conv fill:#BF8700,stroke:#BF8700,color:#fff
  class UTILS,FR arch
  class PAGES crit
  class UI,D1,D2,D7,D3,D4,D5,D6 conv
```

## Adding a person to the site

The whole point of the design: one row of TOML, and both language sites update.

```mermaid
sequenceDiagram
  actor M as Lab member
  participant T as _data/team.toml
  participant U as utils.jl
  participant F as Franklin
  participant S as Live site

  M->>T: add [[person]] with name_en, name_zh,<br/>status, last_verified
  M->>F: git push to main
  F->>U: call hfun_team_members()
  U->>T: read the file (cached once per build)
  U->>U: warn if last_verified > 12 months old
  U->>U: pick() -> name_en on /team/, name_zh on /zh/team/
  U-->>F: HTML for BOTH languages
  F->>F: check for unresolved {{...}} calls
  F->>S: publish to gh-pages
  Note over S: The card appears on /team/ and /zh/team/.<br/>No HTML was written by anyone.
```

## What the news slider does, and for whom

The one piece of behaviour on this site that changes by visitor. It exists because a slider that
moves on its own is exactly what a reduced-motion preference is meant to stop.

```mermaid
sequenceDiagram
  actor V as Visitor
  participant P as Page
  participant JS as news-slider.js
  participant S as Slider

  V->>P: opens the home page
  P->>JS: DOMContentLoaded
  JS->>JS: read prefers-reduced-motion

  alt motion is fine
    JS->>S: show slide 0, fill the progress line over 6 s
    JS->>S: advance, and repeat
    V->>S: hovers or focuses
    S->>JS: pause while reading
    V->>S: leaves
    S->>JS: resume
  else visitor asked for reduced motion
    JS->>S: show slide 0 and STOP
    Note over S: no auto-advance, no filling bar,<br/>arrows and title navigation still work
  end

  V->>S: clicks an arrow or a title
  S->>JS: go to that slide, restart the timer
```
