# Test Setup Slide Import Design

Date: 2026-08-30

## Objective

Convert the equipment material in `CCWANG LAB Test Setup - Aug 2026` into public facility and project pages. The website must present extracted figures and selectable text, never complete slide images. Source wording, fonts, colors, and verified technical claims remain unchanged.

## Source boundaries

The source contains 31 rasterized JPEG slides at 1280 × 720 pixels.

- Slide 1 is a cover and is not published as content.
- Slides 2–30 contain equipment or research material.
- Slide 31 is a thank-you/contact slide and is not published as content.
- Slides 5–6, 9–10, and 21–22 describe three multi-slide subjects and are consolidated.

This produces 26 canonical pages: 14 facilities and 12 projects.

## Content map

### Facilities

| Slides | Canonical ID | Working title | Layout |
|---:|---|---|:---:|
| 2 | `falling-film-cooling-system` | Two-phase falling-film cooling system | C |
| 7 | `thermal-fin-natural-convection-chamber` | Thermal-fin natural-convection chamber | A |
| 8 | `air-cooler-wind-tunnel` | Wind tunnel for air-cooled heat sinks | B |
| 9–10 | `data-center-air-cooling-facility` | Experimental data-center facility | C |
| 11 | `two-phase-cold-plate-test-platform` | Two-phase cold plate cooling test platform | A |
| 12 | `flooded-evaporator-test-rig` | Flooded evaporator test rig | B |
| 13 | `boiler-surface-test-rig` | Boiler-surface experiment setup | C |
| 15 | `three-kilowatt-cold-plate-test-facility` | Two-phase cold plate test facility | A |
| 16 | `vapor-compression-cooling-system` | Vapor-compression refrigeration cooling system | B |
| 17 | `refrigerant-lubricant-boiling-system` | Single-tube boiling test system | C |
| 18 | `liquid-desiccant-air-conditioning-system` | Liquid-desiccant air-conditioning system | A |
| 28 | `carvera-desktop-cnc` | Carvera desktop CNC machine | B |
| 29 | `fabrication-and-microscopy-equipment` | Fabrication and microscopy equipment | C |
| 30 | `amca-wind-tunnel` | AMCA wind tunnel and environmental control room | A |

### Projects

| Slides | Canonical ID | Working title | Layout |
|---:|---|---|:---:|
| 3 | `gaming-laptop-hybrid-vapor-chamber` | Hybrid vapor-chamber heat-pipe module for gaming laptops | A |
| 4 | `two-phase-closed-loop-thermosyphon` | Two-phase closed-loop thermosyphon cooling system | B |
| 5–6 | `chip-package-lid-thermal-spreading` | Thermal spreading of chip-package lids | C |
| 14 | `heat-pipes-freezing-conditions` | Heat pipes under freezing conditions | A |
| 19 | `immersion-cooling-microchannel-lid` | Immersion-cooling microchannel lid cold plate | B |
| 20 | `oil-immersion-heat-transfer-enhancement` | Heat-transfer enhancement in oil-immersion cooling | C |
| 21–22 | `multi-agent-server-cooling-control` | 2U server experimental platform with multi-agent control | A |
| 23 | `pulsating-jet-impingement` | Pulsating jet impingement | B |
| 24 | `expansion-tank-pre-charge-pressure` | Expansion-tank pre-charge pressure | C |
| 25 | `embedded-microfluidic-interlayer-cooling` | Embedded microfluidic interlayer cooling | A |
| 26 | `supercritical-co2-chiller` | Two-stage supercritical CO₂ chiller | B |
| 27 | `thermosyphon-working-fluid-filling-ratio` | Thermosyphon working-fluid and filling-ratio study | C |

Working titles identify the records. The final visible titles are transcribed from the source slides without rewriting.

## Classification rule

A reusable rig, chamber, instrument, fabrication tool, or measurement platform is a facility. A study framed around a research question, comparison, intervention, or measured effect is a project. A multi-slide subject becomes one page when the later slide continues the same apparatus or analysis.

The project data model will allow `student` to be omitted. An imported project receives a researcher byline only when the source identifies a verified person. No researcher association is inferred from lab ownership.

## Content and language

Titles, narrative paragraphs, bullets, captions, status labels, dimensions, operating conditions, equipment names, and links are manually transcribed from the full-resolution source. Punctuation, units, symbols, trademark marks, and source capitalization are retained.

The source supplies English only. To honor the instruction to keep wording unchanged, the English source text is stored in both `_en` and `_zh` fields. Chinese navigation and interface labels remain localized, but no technical translation is invented.

The cover, university marks, lab logo, page numbers, and thank-you/contact slide are not imported into content pages.

## Figure extraction

Each photograph, schematic, chart, sample image, and equipment diagram is extracted as its own asset. Crops exclude slide titles, narrative text, captions, logos, decorative bands, and page numbers. Captions and explanatory text render as HTML.

Asset paths use `_assets/img/test-setups/<canonical-id>/figure-<nn>.<ext>`. Photographs remain JPEG at high quality. Line drawings, charts, and diagrams use PNG. Assets are not upscaled. No generative image processing is used.

The first representative landscape figure becomes the listing thumbnail. Technical drawings use the existing data-driven contained-thumbnail treatment so labels are not cropped in either theme.

## Page architecture

Every subject receives one English and one Chinese canonical route:

- `/facilities/<id>/` and `/zh/facilities/<id>/` for facilities.
- `/projects/<id>/` and `/zh/projects/<id>/` for projects.

The existing A, B, and C compositions become shared setup-page templates. A record stores `layout = "a"`, `"b"`, or `"c"`; the renderer uses one semantic DOM and changes only layout CSS. The templates are distributed 9 A, 8 B, and 9 C across the 26 pages.

- A pairs a figure-led gallery with supporting narrative.
- B leads with narrative and gives wide technical drawings priority.
- C uses a narrative column beside a mixed photo-and-diagram rail.

Mobile order is title, narrative, figures, and captions for every template. Narrative text retains the site measure and justified alignment. Figures use their natural aspect ratio and full-width technical media remain legible.

Facility listing cards become links to their canonical pages. Existing project pages and project-card behavior remain unchanged. Imported project pages use the shared setup renderer; existing hand-written Markdown project pages continue using their current renderer.

The temporary `/facility-designs/` comparison and three falling-film duplicate routes are removed after the canonical falling-film page is present. The A, B, and C template CSS remains available for all records.

## Data model

Facility and imported-project records carry:

- `id`, `area`, `image`, `image_fit`, and `layout`.
- Bilingual `title`, `lead`, and `body` fields.
- `source_slides`, retained as provenance metadata and not rendered.
- Nested figures with `id`, `kind`, `image`, and bilingual captions.
- Optional structured fact or bullet rows only when the source presents them as such.

Project `student` remains supported but becomes optional. Existing records with students retain their current bylines and validation.

## Failure handling

The build stops when a layout is outside A/B/C, a referenced research area is missing, a figure list is empty, an image path is absent, an image-fit value is invalid, a provided student ID is invalid, or an imported record lacks a canonical page in either language.

Placeholder records continue to be filtered. Source uncertainty is preserved as source wording such as “Status: In Progress” or “Status: Under construction”; it is not resolved by inference.

## Implementation sequence

1. Generalize the pilot renderer and data validation while preserving the existing falling-film page.
2. Add a manifest audit for the 26 records, routes, source-slide grouping, assets, and layouts.
3. Import facilities in small batches, extracting figures and transcribing source text.
4. Make project researcher references optional and import project batches.
5. Replace the temporary falling-film comparison routes with the canonical route.
6. Rebuild and perform automated and visual regression checks.

Each batch remains reviewable and must leave the site buildable.

## Verification

The import audit verifies:

- Exactly 14 imported facilities and 12 imported projects exist.
- Every imported record has English and Chinese canonical routes.
- Slide groups 5–6, 9–10, and 21–22 are consolidated once.
- Slides 1 and 31 are absent from published content.
- No published asset is byte-identical to any complete source slide.
- No `Slide*.jpg` path or complete-slide reference appears in generated HTML.
- Every figure asset exists and every page contains its record's figures and captions.
- Layout distribution is 9 A, 8 B, and 9 C.
- Optional project bylines appear only when a verified student ID is present.
- Canonical pages are indexable and included in the sitemap.

Franklin `optimize()` must complete. The facility, project, public-content, partner, profile, contrast, unresolved-template, source-status, and Git whitespace checks must pass. `python scripts/shoot.py --measure` must report `AUDIT CLEAN`.

Every imported page is captured at 1440 px in light theme and inspected in contact sheets. At least one page per layout and content type is also inspected at 492 px and in dark theme. True 320, 360, and 390 px widths remain manual checks because the local Edge harness cannot render narrower than 492 CSS pixels accurately.

## Non-goals

This import does not rewrite source claims, translate technical prose, invent researchers, add publications, change fonts or colors, alter sponsor behavior, deploy the site, or process unrelated placeholder content.
