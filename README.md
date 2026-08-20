# CC Wang Lab

Website for Prof. Chi-Chuan Wang's thermal engineering laboratory at National Yang Ming Chiao Tung
University. English and Traditional Chinese. Built with [Franklin.jl](https://franklinjl.org).

**Live at** https://cc-wang-lab.github.io/

## Run it locally

```bash
julia --project=. -e 'using Pkg; Pkg.instantiate()'   # once per machine
julia --project=. -e 'using Franklin; serve()'        # http://localhost:8000
```

## Editing content

**You never write HTML.** Every list on the site is generated from a `.toml` file in `_data/`.
Add a row, push, and both language versions update.

Read [docs/how-to-edit.md](docs/how-to-edit.md). It is written for lab members, not developers.

## Publishing

Push to `main`. The GitHub Action builds the site and publishes it to `gh-pages`, about three
minutes later.

**One manual step, once:** repo Settings → Pages → Source → Deploy from a branch → `gh-pages` / root.

## Documentation

| File | What it covers |
|---|---|
| [docs/how-to-edit.md](docs/how-to-edit.md) | Adding people, papers, news. For lab members. |
| [docs/architecture.md](docs/architecture.md) | The four diagrams: rules, branches, build, workflow. |
| [docs/reference/design-decisions.md](docs/reference/design-decisions.md) | Every design choice, with its reason. |
| [docs/reference/video-guide.md](docs/reference/video-guide.md) | The hero video: measurements, ffmpeg recipes, what to film next. |

## Before this goes public

- [ ] Replace the placeholder logo with the real file (SVG preferred)
- [ ] Replace the favicons — they are currently the developer's own
- [ ] Native Traditional Chinese review of every page
- [ ] Real team photos, names and topics in `_data/team.toml`
- [ ] Delete the three PLACEHOLDER items in `_data/news.toml`
- [ ] Add 15–20 recent (2022–2026) electronics-cooling and two-phase papers
- [ ] Confirm Prof. Wang's email and extension are correct

---

Developed by Maysam Gholampour — meysam.gholampoor@gmail.com
