# Archived profile layout variants

The site used four profile presentations during design review:

- A — Editorial: portrait and biography paired with the academic record.
- B — Dossier: compact identity followed by facts and biography.
- C — Narrative-first: biography-led reading column with a supporting rail.
- D — Header profile: compact identity and portrait inside the page header.

D was selected on 2026-08-30. A, B and C are no longer emitted by Franklin, and the temporary
comparison routes and query-string controller were removed from the public site.

Git is the canonical archive because it preserves the templates, generated helpers, controller,
styles, localized labels and regression coverage together. The main recovery points are:

- `0466915` — shared A/B/C profile variants and comparison interface.
- `f27ad01` — D header profile introduced alongside A/B/C.
- `4efd141` — D identity rows refined.
- `799554a` — D expertise label simplified and sponsor logos restored.

Inspect any archived file without changing the working tree with, for example:

```sh
git show 4efd141:_assets/js/profile-layout.js
git show 4efd141:profile-designs.md
git show 4efd141:_css/style.css
```

If another layout is reconsidered, restore it on a separate review branch rather than copying
individual declarations into the live D-only implementation.
