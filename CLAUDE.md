# CLAUDE.md — CC-Wang-Lab.github.io

Bilingual website for Prof. Chi-Chuan Wang's thermal engineering lab at NYCU.
Franklin.jl, Bootstrap 5.3, deployed to GitHub Pages.

## Global rules, in short

- **Plain English.** Answer first. Numbers in tables. One idea per sentence. No paired dashes
  bracketing a clause. Full rules: [~/.claude/rules/plain_english.md](../../../Users/Maysam/.claude/rules/plain_english.md).
- **Verify before claiming.** Never invent a function, a version or a fact. Check the source.
- **Scope discipline.** Simplest working approach first. Do not refactor what was not asked for.
- **Branch discipline.** Stay on the current branch. Never create or switch branches without asking.
  Merges use `--no-ff`.
- **Commits.** No AI attribution. No `Co-Authored-By`, no generated-with footer.
- **Golden files.** Never modify or regenerate a baseline or snapshot without explicit approval.
- **Shell.** Prefer the Bash tool with Unix syntax. PowerShell only when bash fails on Windows.
- **New GUI elements must look native.** Match the control beside them, not the framework default.

## Quick reference

| Want to… | Do this |
|---|---|
| Preview locally | `julia --project=. -e 'using Franklin; serve()'` → http://localhost:8000 |
| First run on a machine | `julia --project=. -e 'using Pkg; Pkg.instantiate()'` |
| Add a person, paper, news item, sector | Edit the matching file in `_data/`. **Never edit HTML.** |
| Change any interface word | `_data/ui.toml` — both languages live side by side |
| Add a page | Create `x.md` AND `zh/x.md`, then add it to `NAV` in `utils.jl` |
| Change how something renders | The matching `hfun_*` in `utils.jl` |
| Change colour or type | `_css/style.css` |
| Deploy | Push to `main`. The Action publishes to `gh-pages`. |

## Rules

- [Franklin build and serve](.claude/rules/franklin-serve.md) — the serve command, flags, what not to commit
- [Bilingual pages](.claude/rules/bilingual.md) — mirrored folders, `{{url}}`, `{{ui}}`, the CJK font trap
- [Data files](.claude/rules/data-files.md) — the one hard rule of this repo, and the staleness check
- [Media](.claude/rules/media.md) — hero video budget, ffmpeg recipes, the GitHub Pages bandwidth limit

## The one thing to remember

**Every list on this site is generated from `_data/` at build time.** People, publications, news,
research areas, capabilities, sectors. A lab member adds a row to a TOML file and the page grows
itself, in both languages. If you find yourself writing a `<div>` for a person or a paper, stop —
the generator is in `utils.jl` and it is the thing to change.

## Docs

- [docs/architecture.md](docs/architecture.md) — the diagrams
- [docs/how-to-edit.md](docs/how-to-edit.md) — for lab members, not developers
- [docs/reference/design-decisions.md](docs/reference/design-decisions.md) — every choice, with its reason
- [docs/reference/video-guide.md](docs/reference/video-guide.md) — the hero video, measured
- [docs/reference/chatgpt-round1.md](docs/reference/chatgpt-round1.md), [round2](docs/reference/chatgpt-round2.md) — the outside critique
