# Test Setup Slide Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert Slides 2–30 of the August 2026 CC Wang Lab test-setup source into 14 canonical facility pages and 12 canonical project pages using extracted figures, verbatim selectable text, and a balanced A/B/C layout distribution.

**Architecture:** Facility and imported-project records keep source text, provenance, figure metadata, and a layout key in TOML. One shared Julia renderer emits the semantic page DOM for both content types, while three CSS compositions arrange it. A reproducible ImageMagick script extracts individual figures; focused Python audits validate records, routes, assets, hashes, wording contracts, bylines, sitemap state, and layout distribution.

**Tech Stack:** Franklin.jl, Julia, TOML, HTML, CSS, Python 3 standard library, PowerShell 7, ImageMagick, headless Microsoft Edge.

**Spec:** `docs/superpowers/specs/2026-08-30-test-setup-import-design.md`

## Global Constraints

- Preserve every source title, paragraph, bullet, caption, unit, symbol, trademark mark, status label, dimension, equipment name, and URL verbatim.
- Store the English source wording in both `_en` and `_zh` fields; do not invent technical translations.
- Never publish a complete 1280 × 720 source slide, slide logo, page number, cover, or thank-you slide.
- Extract photographs as high-quality JPEG and diagrams/charts as PNG without upscaling or generative processing.
- Keep ET Book, Noto Serif TC, the existing color tokens, the existing type scale, and unrelated routes unchanged.
- Keep narrative width at `--measure`, justify narrative paragraphs, and preserve 44 px controls.
- Make project `student` optional; render a byline only for an explicit, valid, public team ID.
- Every content batch ends with a successful Franklin build and focused audit before commit.
- Do not push, deploy, merge, switch branches, or alter `main`.

---

## File Structure

### Shared implementation

- Modify `_data/facilities.toml`: facility records, layouts, provenance, figures, and listing thumbnails.
- Modify `_data/projects.toml`: imported-project records, optional students, layouts, provenance, and figures.
- Modify `utils.jl`: shared setup renderer, record validation, optional project bylines, canonical facility links.
- Modify `_css/style.css`: shared `.setup-study` templates A/B/C and contained technical media.
- Create `scripts/extract-test-setup-assets.ps1`: reproducible crop commands parameterized by the source-slide directory.
- Create `scripts/check-setup-renderer.py`: focused canonical-renderer and optional-byline regression checks.
- Create `scripts/check-test-setup-import.py`: literal 26-record import manifest and built-site integrity audit.
- Modify `scripts/check-public-site.py`: canonical facility/project population and noindex expectations.
- Modify `docs/how-to-edit.md`: document `layout`, `source_slides`, nested figures, optional captions, and optional project students.

### Generated source assets

- Create `_assets/img/test-setups/<canonical-id>/figure-<nn>.jpg` for photographs.
- Create `_assets/img/test-setups/<canonical-id>/figure-<nn>.png` for diagrams, charts, and line drawings.

### Canonical routes

- Create 14 files under `facilities/<id>.md` and matching files under `zh/facilities/<id>.md`.
- Create 12 files under `projects/<id>.md` and matching files under `zh/projects/<id>.md`.
- Delete the temporary `facility-designs.md` and three `facilities/falling-film-cooling-{a,b,c}.md` routes only after the canonical falling-film route passes.

---

### Task 1: Canonical Shared Setup Renderer

**Files:**
- Create: `scripts/check-setup-renderer.py`
- Create: `facilities/falling-film-cooling-system.md`
- Create: `zh/facilities/falling-film-cooling-system.md`
- Modify: `_data/facilities.toml`
- Modify: `utils.jl:875-989`
- Modify: `_css/style.css:2100-2290`

**Interfaces:**
- Consumes: `pick(record, field)`, `area_by_id(id, src)`, `prefix()`, existing nested `figure` rows.
- Produces: `render_setup_page(record::AbstractDict, kind::AbstractString)::String`, `hfun_facility_page()::String`, and shared `.setup-study--a|b|c` CSS.

- [ ] **Step 1: Write the failing renderer audit**

Create `scripts/check-setup-renderer.py` with literal expectations for the canonical falling-film route:

```python
EXPECTED = {
    "id": "falling-film-cooling-system",
    "layout": "c",
    "routes": (
        "facilities/falling-film-cooling-system/index.html",
        "zh/facilities/falling-film-cooling-system/index.html",
    ),
    "figures": (
        "/assets/img/facilities/falling-film-cooling-100w.jpg",
        "/assets/img/facilities/falling-film-cooling-500w.jpg",
        "/assets/img/facilities/falling-film-cooling-cabinet.png",
        "/assets/img/facilities/falling-film-cooling-dimensions.png",
    ),
}
```

Parse each built route with `html.parser.HTMLParser`. Assert one `.setup-study`, one `.setup-study--c`, four `.setup-study-figure` nodes, all four image paths once, no robots `noindex`, and the route in `sitemap.xml`. Assert `/facilities/` links to the English canonical route and `/zh/facilities/` links to the Chinese canonical route.

- [ ] **Step 2: Run the renderer audit and verify RED**

Run:

```powershell
python scripts/check-setup-renderer.py
```

Expected: `SETUP RENDERER AUDIT FAILED` because the canonical routes and shared classes do not exist.

- [ ] **Step 3: Store the chosen layout in data**

Add these fields to the existing falling-film record:

```toml
layout = "c"
source_slides = [2]
```

Retain the existing verbatim title, lead, body, four figures, cabinet thumbnail, and `image_fit = "contain"`.

Use the following optional source-section shape for later records that contain headings, paragraphs, or bullet lists:

```toml
[[item.section]]
heading_en = "Main Function"
heading_zh = "Main Function"
body_en = ""
body_zh = ""
items_en = ["Evaluate two-phase cold plates", "Control flow rate, pressure, and fluid temperature"]
items_zh = ["Evaluate two-phase cold plates", "Control flow rate, pressure, and fluid temperature"]
```

Imported projects use `[[project.section]]` with the same fields. Empty headings/bodies are permitted; empty list items are not.

- [ ] **Step 4: Generalize the renderer**

In `utils.jl`, implement the shared boundary:

```julia
function setup_layout(record::AbstractDict, src::AbstractString)
    layout = lowercase(String(get(record, "layout", "")))
    layout in ("a", "b", "c") ||
        error("$src: layout for '$(record["id"])' must be a, b or c")
    return layout
end

function render_setup_sections(record::AbstractDict)
    blocks = String[]
    for section in get(record, "section", Any[])
        heading = strip(pick(section, "heading"))
        body = strip(pick(section, "body"))
        items = get(section, "items_" * lang(), get(section, "items_en", Any[]))
        heading_html = isempty(heading) ? "" : "<h2>$(esc(heading))</h2>"
        body_html = isempty(body) ? "" : "<p>$(esc(body))</p>"
        items_html = isempty(items) ? "" :
            "<ul>" * join(["<li>$(esc(item))</li>" for item in items]) * "</ul>"
        push!(blocks, "<section>$(heading_html)$(body_html)$(items_html)</section>")
    end
    return join(blocks, "\n")
end

function render_setup_page(record::AbstractDict, kind::AbstractString)
    src = kind == "facility" ? "facilities.toml" : "projects.toml"
    layout = setup_layout(record, src)
    figures = get(record, "figure", Any[])
    isempty(figures) && error("$src: '$(record["id"])' needs at least one figure")
    back_path = kind == "facility" ? "/facilities/" : "/projects/"
    back_html = kind == "facility" ?
        "&larr; " * esc(ui("nav", "facilities")) : esc(ui("projects", "back"))
    area = area_by_id(String(record["area"]), src)
    title = esc(pick(record, "title"))
    figure_html = join([render_setup_figure(figure) for figure in figures], "\n")
    return """
<header class="page-hd setup-study-hd"><div class="container">
  <p class="project-crumb"><a href="$(prefix())$(back_path)">$(back_html)</a></p>
  <span class="card-badge">$(esc(pick(area, "title")))</span>
  <h1>$(title)</h1>
</div></header>
<div class="page-body setup-study-page"><div class="container">
  <article class="setup-study setup-study--$(layout)">
    <div class="setup-study-copy prose">
      <p>$(esc(pick(record, "body")))</p>
      $(render_setup_sections(record))
    </div>
    <div class="setup-study-figures">$(figure_html)</div>
  </article>
</div></div>"""
end
```

Implement `render_setup_figure(figure::AbstractDict)::String` beside these functions. It emits `.setup-study-figure--<id>` and `.setup-study-figure--<kind>`, the image, and a `figcaption` only when `pick(figure, "caption")` is non-empty. Keep empty image alt text when the adjacent caption identifies the figure. Rename the pilot DOM classes from `.facility-study*` to `.setup-study*` and read layout from the record instead of page front matter.

- [ ] **Step 5: Make facility cards canonical links**

Change `hfun_facilities()` so each public facility card is an `<a class="card-media">` to `prefix() * "/facilities/" * f["id"] * "/"`. Retain `image_fit` validation and the contained-thumbnail modifier.

- [ ] **Step 6: Add mirrored canonical route stubs**

English:

```markdown
+++
title = "Two-phase falling-film cooling system"
facility = "falling-film-cooling-system"
lang = "en"
+++

~~~
{{facility_page}}
~~~
```

Chinese uses the same title and `facility`, with `lang = "zh"`.

- [ ] **Step 7: Rebuild and verify GREEN**

Run:

```powershell
julia --project=. -e "using Franklin; optimize()"
python scripts/check-setup-renderer.py
python scripts/check-facility-layouts.py
```

Expected: Franklin exits 0; both audits report clean.

- [ ] **Step 8: Commit the renderer foundation**

```powershell
git add _data/facilities.toml utils.jl _css/style.css scripts/check-setup-renderer.py scripts/check-facility-layouts.py scripts/check-public-site.py _assets/img/facilities/falling-film-cooling-100w.jpg _assets/img/facilities/falling-film-cooling-500w.jpg _assets/img/facilities/falling-film-cooling-cabinet.png _assets/img/facilities/falling-film-cooling-dimensions.png facilities/falling-film-cooling-system.md zh/facilities/falling-film-cooling-system.md
git commit -m "Generalize canonical setup page rendering"
```

---

### Task 2: Core Airflow and Data-Center Facilities

**Files:**
- Create: `scripts/extract-test-setup-assets.ps1`
- Create: `scripts/check-test-setup-import.py`
- Modify: `_data/facilities.toml`
- Create routes and assets for `thermal-fin-natural-convection-chamber`, `air-cooler-wind-tunnel`, and `data-center-air-cooling-facility` in both languages.

**Interfaces:**
- Consumes: `render_setup_page`, `layout`, `source_slides`, nested figures.
- Produces: the reusable extraction script and the first literal import-manifest audit.

- [ ] **Step 1: Write the failing batch manifest**

Create `scripts/check-test-setup-import.py` with these literal records:

```python
EXPECTED = {
    "facility": {
        "falling-film-cooling-system": ([2], "c", "two-phase", 4),
        "thermal-fin-natural-convection-chamber": ([7], "a", "heat-exchangers", 1),
        "air-cooler-wind-tunnel": ([8], "b", "electronics-cooling", 1),
        "data-center-air-cooling-facility": ([9, 10], "c", "data-center", 7),
    },
    "project": {},
}
```

Use `tomllib` to verify record fields and figure counts. Verify English/Chinese route files in `__site`, every referenced source asset under `_assets`, matching `.setup-study--<layout>` in HTML, both routes in the sitemap, and no source filename matching `Slide*.jpg` in generated HTML.

- [ ] **Step 2: Run the batch audit and verify RED**

```powershell
python scripts/check-test-setup-import.py
```

Expected: failures naming the three absent facility records.

- [ ] **Step 3: Build the reproducible extraction script**

Create a parameterized script:

```powershell
param(
    [Parameter(Mandatory = $true)]
    [string]$SourceDir
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$outputRoot = Join-Path $repoRoot '_assets\img\test-setups'

function Export-Crop {
    param([int]$Slide, [string]$Geometry, [string]$RelativePath)
    $source = Join-Path $SourceDir ("Slide{0}.jpg" -f $Slide)
    $target = Join-Path $outputRoot $RelativePath
    New-Item -ItemType Directory -Force (Split-Path -Parent $target) | Out-Null
    & magick $source -crop $Geometry +repage $target
    if ($LASTEXITCODE -ne 0) { throw "ImageMagick failed for Slide $Slide" }
}
```

Inspect Slides 7–10 at original resolution. Add one explicit `Export-Crop` line for the Slide 7 chamber, one for the Slide 8 panoramic wind tunnel, and seven for the data-center diagrams/photos across Slides 9–10. Use PNG for meshes, diagrams, and rack renderings; use JPEG quality 95 for photographs by adding `-quality 95` inside `Export-Crop` when the target extension is `.jpg`.

- [ ] **Step 4: Extract and visually inspect the ten figures**

```powershell
& scripts/extract-test-setup-assets.ps1 -SourceDir 'C:\Users\Maysam\Downloads\ChromeDL\CCWANG LAB Test Setup - Aug 2026'
```

Create a temporary contact sheet with ImageMagick and inspect it with `view_image`. Reject crops containing slide headers, narrative paragraphs, logos, captions, or page numbers.

- [ ] **Step 5: Add the three facility records and mirrored routes**

Use the exact source titles and narratives from Slides 7–10. Store identical English text in `_en` and `_zh`. Use these fixed assignments:

```toml
# Slide 7
area = "heat-exchangers"
layout = "a"
source_slides = [7]

# Slide 8
area = "electronics-cooling"
layout = "b"
source_slides = [8]

# Slides 9–10
area = "data-center"
layout = "c"
source_slides = [9, 10]
```

Captions are verbatim when the slide provides them and empty otherwise. Use a complete landscape diagram/photo as each card image; set `image_fit = "contain"` for technical drawings.

- [ ] **Step 6: Rebuild, verify, and commit**

```powershell
julia --project=. -e "using Franklin; optimize()"
python scripts/check-test-setup-import.py
python scripts/check-setup-renderer.py
git add scripts/extract-test-setup-assets.ps1 scripts/check-test-setup-import.py _data/facilities.toml _assets/img/test-setups/thermal-fin-natural-convection-chamber _assets/img/test-setups/air-cooler-wind-tunnel _assets/img/test-setups/data-center-air-cooling-facility facilities/thermal-fin-natural-convection-chamber.md facilities/air-cooler-wind-tunnel.md facilities/data-center-air-cooling-facility.md zh/facilities/thermal-fin-natural-convection-chamber.md zh/facilities/air-cooler-wind-tunnel.md zh/facilities/data-center-air-cooling-facility.md
git commit -m "Import airflow and data-center facilities"
```

---

### Task 3: Boiling and Cold-Plate Facilities

**Files:**
- Modify: `scripts/check-test-setup-import.py`
- Modify: `scripts/extract-test-setup-assets.ps1`
- Modify: `_data/facilities.toml`
- Create routes/assets for `two-phase-cold-plate-test-platform`, `flooded-evaporator-test-rig`, and `boiler-surface-test-rig`.

**Interfaces:**
- Consumes: the extraction helper and import audit from Task 2.
- Produces: three facility records with 9 figures.

- [ ] **Step 1: Extend the manifest and verify RED**

Add:

```python
"two-phase-cold-plate-test-platform": ([11], "a", "two-phase", 1),
"flooded-evaporator-test-rig": ([12], "b", "two-phase", 2),
"boiler-surface-test-rig": ([13], "c", "two-phase", 6),
```

Run `python scripts/check-test-setup-import.py`. Expected: the new IDs and routes are absent.

- [ ] **Step 2: Extract Slides 11–13**

Add explicit crop calls for the annotated cold-plate platform photo; the flooded-evaporator system and close-up; four boiler-surface samples, the test schematic, and the rig photo. Keep labels that belong inside a technical diagram, but move surrounding captions and narrative into data.

- [ ] **Step 3: Add exact data and mirrored routes**

Use areas/layouts from the manifest. Preserve Slide 11 headings such as “Main Function” and “Flow Path” as structured fact/bullet rows rather than flattening them into a screenshot. Preserve Slide 13 surface-treatment labels as captions attached to their corresponding extracted samples.

- [ ] **Step 4: Rebuild, verify, inspect, and commit**

```powershell
julia --project=. -e "using Franklin; optimize()"
python scripts/check-test-setup-import.py
python scripts/shoot.py --url /facilities/boiler-surface-test-rig/ --width 1440 --theme light --motion off --measure
git add scripts/check-test-setup-import.py scripts/extract-test-setup-assets.ps1 _data/facilities.toml _assets/img/test-setups/two-phase-cold-plate-test-platform _assets/img/test-setups/flooded-evaporator-test-rig _assets/img/test-setups/boiler-surface-test-rig facilities/two-phase-cold-plate-test-platform.md facilities/flooded-evaporator-test-rig.md facilities/boiler-surface-test-rig.md zh/facilities/two-phase-cold-plate-test-platform.md zh/facilities/flooded-evaporator-test-rig.md zh/facilities/boiler-surface-test-rig.md
git commit -m "Import boiling and cold-plate facilities"
```

---

### Task 4: Refrigeration and Dehumidification Facilities

**Files:**
- Modify: `scripts/check-test-setup-import.py`
- Modify: `scripts/extract-test-setup-assets.ps1`
- Modify: `_data/facilities.toml`
- Create routes/assets for `three-kilowatt-cold-plate-test-facility`, `vapor-compression-cooling-system`, `refrigerant-lubricant-boiling-system`, and `liquid-desiccant-air-conditioning-system`.

**Interfaces:**
- Consumes: shared facility renderer and structured source rows.
- Produces: four facility records with 10 figures.

- [ ] **Step 1: Extend the manifest and verify RED**

```python
"three-kilowatt-cold-plate-test-facility": ([15], "a", "two-phase", 2),
"vapor-compression-cooling-system": ([16], "b", "hvacr", 2),
"refrigerant-lubricant-boiling-system": ([17], "c", "two-phase", 3),
"liquid-desiccant-air-conditioning-system": ([18], "a", "hvacr", 3),
```

Run the audit and confirm the four-record failure.

- [ ] **Step 2: Extract Slides 15–18**

Extract the Slide 15 rig photo and flow diagram; two Slide 16 system photographs; the Slide 17 apparatus photo, flow diagram, and heater diagram; and the Slide 18 rig photograph, perspective system diagram, and process-flow diagram.

- [ ] **Step 3: Add exact data and mirrored routes**

Transcribe the source paragraphs, yellow callouts, diagram captions, working-fluid information, dimensions, and operating conditions exactly. Use a contained landscape technical figure for every listing card.

- [ ] **Step 4: Rebuild, verify, inspect, and commit**

```powershell
julia --project=. -e "using Franklin; optimize()"
python scripts/check-test-setup-import.py
python scripts/shoot.py --url /facilities/liquid-desiccant-air-conditioning-system/ --width 492 --theme dark --motion off --measure
git add scripts/check-test-setup-import.py scripts/extract-test-setup-assets.ps1 _data/facilities.toml _assets/img/test-setups/three-kilowatt-cold-plate-test-facility _assets/img/test-setups/vapor-compression-cooling-system _assets/img/test-setups/refrigerant-lubricant-boiling-system _assets/img/test-setups/liquid-desiccant-air-conditioning-system facilities/three-kilowatt-cold-plate-test-facility.md facilities/vapor-compression-cooling-system.md facilities/refrigerant-lubricant-boiling-system.md facilities/liquid-desiccant-air-conditioning-system.md zh/facilities/three-kilowatt-cold-plate-test-facility.md zh/facilities/vapor-compression-cooling-system.md zh/facilities/refrigerant-lubricant-boiling-system.md zh/facilities/liquid-desiccant-air-conditioning-system.md
git commit -m "Import refrigeration test facilities"
```

---

### Task 5: Fabrication, Microscopy, and AMCA Facilities

**Files:**
- Modify: `scripts/check-test-setup-import.py`
- Modify: `scripts/extract-test-setup-assets.ps1`
- Modify: `_data/facilities.toml`
- Create routes/assets for `carvera-desktop-cnc`, `fabrication-and-microscopy-equipment`, and `amca-wind-tunnel`.

**Interfaces:**
- Consumes: setup renderer and contained listing media.
- Produces: final three facility records; facility count becomes 14.

- [ ] **Step 1: Extend the manifest and verify RED**

```python
"carvera-desktop-cnc": ([28], "b", "electronics-cooling", 1),
"fabrication-and-microscopy-equipment": ([29], "c", "electronics-cooling", 3),
"amca-wind-tunnel": ([30], "a", "heat-exchangers", 1),
```

Run the audit and confirm three absent records.

- [ ] **Step 2: Extract Slides 28–30**

Extract the CNC photograph; the 3D-printer photograph and two microscope photographs; and the AMCA wind-tunnel/environmental-room photograph. Exclude all slide logos and page numbers.

- [ ] **Step 3: Add exact data and mirrored routes**

Render Slide 28 status, dimensions, weight, spindle power/speed, and source link as HTML facts. Preserve the two identical “Microscope” source labels on Slide 29. Preserve Slide 30 operating range and data-acquisition wording exactly.

- [ ] **Step 4: Verify the facility total and commit**

```powershell
julia --project=. -e "using Franklin; optimize()"
python scripts/check-test-setup-import.py
python scripts/check-public-site.py
git add scripts/check-test-setup-import.py scripts/extract-test-setup-assets.ps1 _data/facilities.toml _assets/img/test-setups/carvera-desktop-cnc _assets/img/test-setups/fabrication-and-microscopy-equipment _assets/img/test-setups/amca-wind-tunnel facilities/carvera-desktop-cnc.md facilities/fabrication-and-microscopy-equipment.md facilities/amca-wind-tunnel.md zh/facilities/carvera-desktop-cnc.md zh/facilities/fabrication-and-microscopy-equipment.md zh/facilities/amca-wind-tunnel.md
git commit -m "Import fabrication and wind-tunnel facilities"
```

Expected audit state: 14 imported facilities, zero imported projects, layouts A=5, B=4, C=5 for facilities.

---

### Task 6: Optional Project Bylines and Imported-Project Renderer

**Files:**
- Modify: `scripts/check-setup-renderer.py`
- Modify: `_data/projects.toml`
- Modify: `utils.jl:1015-1170`
- Create: `projects/gaming-laptop-hybrid-vapor-chamber.md`
- Create: `zh/projects/gaming-laptop-hybrid-vapor-chamber.md`
- Create assets for Slide 3.

**Interfaces:**
- Consumes: `render_setup_page(record, "project")` from Task 1.
- Produces: `hfun_project_setup_page()::String`; `project_card` and `hfun_project_header` accept absent `student`.

- [ ] **Step 1: Write the failing optional-byline assertions**

Extend `scripts/check-setup-renderer.py` with the Slide 3 project route. Assert the project record has no `student`; generated card/page contain no `.card-by` or `.project-by`; both routes contain `.setup-study--a`; the two extracted images appear; and an existing project with `student = "maysam-gholampour"` still shows its byline.

- [ ] **Step 2: Run and verify RED**

```powershell
python scripts/check-setup-renderer.py
```

Expected: missing Slide 3 project and current code attempts `p["student"]`.

- [ ] **Step 3: Make project students optional**

Use this boundary in both project cards and headers:

```julia
function project_person(project)
    id = get(project, "student", nothing)
    id === nothing && return nothing
    person = person_by_id(String(id))
    return is_public(person) ? person : nothing
end
```

Existing invalid explicit IDs must still stop the build through `person_by_id`. Omitted IDs return `nothing` and render no byline.

- [ ] **Step 4: Add the imported-project wrapper**

```julia
function hfun_project_setup_page()
    id = locvar(:project)
    id === nothing && error("this page needs `project = \"<id>\"` in its front matter")
    hit = filter(p -> p["id"] == String(id), projects())
    isempty(hit) && error("no project with id '$(id)' in projects.toml")
    return render_setup_page(first(hit), "project")
end
```

Imported project stubs call `{{project_setup_page}}`. Existing hand-written projects keep `{{project_header}}`.

- [ ] **Step 5: Import Slide 3 as the first project**

Extract the upper and lower experimental-system photographs. Add a project record with `area = "electronics-cooling"`, `layout = "a"`, `source_slides = [3]`, no `student`, two figures, and exact source title/body in both language fields.

- [ ] **Step 6: Rebuild, verify, and commit**

```powershell
julia --project=. -e "using Franklin; optimize()"
python scripts/check-setup-renderer.py
python scripts/check-profile-layouts.py
git add scripts/check-setup-renderer.py scripts/extract-test-setup-assets.ps1 _data/projects.toml utils.jl _assets/img/test-setups projects/gaming-laptop-hybrid-vapor-chamber.md zh/projects/gaming-laptop-hybrid-vapor-chamber.md
git commit -m "Support imported projects without inferred bylines"
```

---

### Task 7: Thermosyphon, Chip-Lid, and Freezing Projects

**Files:**
- Modify: `scripts/check-test-setup-import.py`
- Modify: `scripts/extract-test-setup-assets.ps1`
- Modify: `_data/projects.toml`
- Create routes/assets for `two-phase-closed-loop-thermosyphon`, `chip-package-lid-thermal-spreading`, and `heat-pipes-freezing-conditions`.

**Interfaces:**
- Consumes: optional-byline project renderer.
- Produces: four total imported projects after this task.

- [ ] **Step 1: Add all four current project expectations and verify RED**

Add the Slide 3 record plus:

```python
"two-phase-closed-loop-thermosyphon": ([4], "b", "two-phase", 3),
"chip-package-lid-thermal-spreading": ([5, 6], "c", "electronics-cooling", 7),
"heat-pipes-freezing-conditions": ([14], "a", "two-phase", 2),
```

Run the import audit and confirm the three new IDs fail.

- [ ] **Step 2: Extract Slides 4–6 and 14**

Extract three Slide 4 apparatus/diagram figures; four Slide 5 sample/test figures; the Slide 6 setup image and two thermal maps; and two Slide 14 apparatus photographs.

- [ ] **Step 3: Add exact data and mirrored routes**

Consolidate Slides 5–6 into one record without duplicating their shared subject title. Preserve Slide 14 status wording, working-fluid statement, subzero temperature range, and yellow source callout exactly.

- [ ] **Step 4: Rebuild, verify, inspect, and commit**

```powershell
julia --project=. -e "using Franklin; optimize()"
python scripts/check-test-setup-import.py
python scripts/shoot.py --url /projects/chip-package-lid-thermal-spreading/ --width 1440 --theme light --motion off --measure
git add scripts/check-test-setup-import.py scripts/extract-test-setup-assets.ps1 _data/projects.toml _assets/img/test-setups/two-phase-closed-loop-thermosyphon _assets/img/test-setups/chip-package-lid-thermal-spreading _assets/img/test-setups/heat-pipes-freezing-conditions projects/two-phase-closed-loop-thermosyphon.md projects/chip-package-lid-thermal-spreading.md projects/heat-pipes-freezing-conditions.md zh/projects/two-phase-closed-loop-thermosyphon.md zh/projects/chip-package-lid-thermal-spreading.md zh/projects/heat-pipes-freezing-conditions.md
git commit -m "Import thermosyphon and chip-lid projects"
```

---

### Task 8: Immersion Cooling and Multi-Agent Server Projects

**Files:**
- Modify: `scripts/check-test-setup-import.py`
- Modify: `scripts/extract-test-setup-assets.ps1`
- Modify: `_data/projects.toml`
- Create routes/assets for `immersion-cooling-microchannel-lid`, `oil-immersion-heat-transfer-enhancement`, and `multi-agent-server-cooling-control`.

**Interfaces:**
- Consumes: project setup renderer and merged-slide provenance.
- Produces: three project records with 13 figures.

- [ ] **Step 1: Extend the manifest and verify RED**

```python
"immersion-cooling-microchannel-lid": ([19], "b", "electronics-cooling", 3),
"oil-immersion-heat-transfer-enhancement": ([20], "c", "electronics-cooling", 5),
"multi-agent-server-cooling-control": ([21, 22], "a", "ai-thermal", 5),
```

- [ ] **Step 2: Extract Slides 19–22**

Extract the Slide 19 apparatus and two cold-plate diagrams; the Slide 20 immersion tank, bubble-enhancement image, and three mechanism diagrams; the Slide 21 server configuration and load-profile chart; and the Slide 22 computational workflow, operating-range diagram, and energy equation.

- [ ] **Step 3: Add exact data and mirrored routes**

Keep diagram labels inside the cropped figures. Render Slide 19 explanatory boxes and Slide 21/22 surrounding prose as HTML. Consolidate Slides 21–22 into one page with `source_slides = [21, 22]`.

- [ ] **Step 4: Rebuild, verify, inspect, and commit**

```powershell
julia --project=. -e "using Franklin; optimize()"
python scripts/check-test-setup-import.py
python scripts/shoot.py --url /projects/multi-agent-server-cooling-control/ --width 492 --theme dark --motion off --measure
git add scripts/check-test-setup-import.py scripts/extract-test-setup-assets.ps1 _data/projects.toml _assets/img/test-setups/immersion-cooling-microchannel-lid _assets/img/test-setups/oil-immersion-heat-transfer-enhancement _assets/img/test-setups/multi-agent-server-cooling-control projects/immersion-cooling-microchannel-lid.md projects/oil-immersion-heat-transfer-enhancement.md projects/multi-agent-server-cooling-control.md zh/projects/immersion-cooling-microchannel-lid.md zh/projects/oil-immersion-heat-transfer-enhancement.md zh/projects/multi-agent-server-cooling-control.md
git commit -m "Import immersion and server-control projects"
```

---

### Task 9: Jet, Expansion-Tank, and Microfluidic Projects

**Files:**
- Modify: `scripts/check-test-setup-import.py`
- Modify: `scripts/extract-test-setup-assets.ps1`
- Modify: `_data/projects.toml`
- Create routes/assets for `pulsating-jet-impingement`, `expansion-tank-pre-charge-pressure`, and `embedded-microfluidic-interlayer-cooling`.

**Interfaces:**
- Consumes: setup layouts B/C/A in sequence.
- Produces: three project records with 10 figures.

- [ ] **Step 1: Extend the manifest and verify RED**

```python
"pulsating-jet-impingement": ([23], "b", "electronics-cooling", 2),
"expansion-tank-pre-charge-pressure": ([24], "c", "hvacr", 4),
"embedded-microfluidic-interlayer-cooling": ([25], "a", "electronics-cooling", 4),
```

- [ ] **Step 2: Extract Slides 23–25**

Extract the Slide 23 setup schematic and response chart; the Slide 24 setup photograph, system diagram, expansion-tank image, and chiller photograph; and the Slide 25 equipment group, working-fluid container, test setup, and remaining distinct equipment figure.

- [ ] **Step 3: Add exact data and mirrored routes**

Preserve Slide 23 numbered cooling concepts, Slide 24 introduction/status/equipment/working-fluid sections, and Slide 25 introduction/status/equipment/working-fluid sections as structured HTML source text. Do not resolve either construction/progress status.

- [ ] **Step 4: Rebuild, verify, inspect, and commit**

```powershell
julia --project=. -e "using Franklin; optimize()"
python scripts/check-test-setup-import.py
python scripts/shoot.py --url /projects/expansion-tank-pre-charge-pressure/ --width 1440 --theme light --motion off --measure
git add scripts/check-test-setup-import.py scripts/extract-test-setup-assets.ps1 _data/projects.toml _assets/img/test-setups/pulsating-jet-impingement _assets/img/test-setups/expansion-tank-pre-charge-pressure _assets/img/test-setups/embedded-microfluidic-interlayer-cooling projects/pulsating-jet-impingement.md projects/expansion-tank-pre-charge-pressure.md projects/embedded-microfluidic-interlayer-cooling.md zh/projects/pulsating-jet-impingement.md zh/projects/expansion-tank-pre-charge-pressure.md zh/projects/embedded-microfluidic-interlayer-cooling.md
git commit -m "Import jet and microfluidic cooling projects"
```

---

### Task 10: CO₂ Chiller and Thermosyphon Projects

**Files:**
- Modify: `scripts/check-test-setup-import.py`
- Modify: `scripts/extract-test-setup-assets.ps1`
- Modify: `_data/projects.toml`
- Create routes/assets for `supercritical-co2-chiller` and `thermosyphon-working-fluid-filling-ratio`.

**Interfaces:**
- Consumes: project renderer, structured facts, source-status preservation.
- Produces: final two project records; imported-project count becomes 12.

- [ ] **Step 1: Extend the manifest and verify RED**

```python
"supercritical-co2-chiller": ([26], "b", "hvacr", 2),
"thermosyphon-working-fluid-filling-ratio": ([27], "c", "two-phase", 1),
```

Run the audit and confirm the two-record failure.

- [ ] **Step 2: Extract Slides 26–27**

Extract the Slide 26 chiller and test-cooler photographs and the Slide 27 complete test-rig photograph. Exclude surrounding text from each crop.

- [ ] **Step 3: Add exact data and mirrored routes**

Preserve Slide 26 description, status, equipment, working-fluid, capacity, and use-case wording. Preserve Slide 27 ongoing-study narrative, status, working fluids, and equipment list.

- [ ] **Step 4: Verify the project total and commit**

```powershell
julia --project=. -e "using Franklin; optimize()"
python scripts/check-test-setup-import.py
python scripts/check-public-site.py
git add scripts/check-test-setup-import.py scripts/extract-test-setup-assets.ps1 _data/projects.toml _assets/img/test-setups/supercritical-co2-chiller _assets/img/test-setups/thermosyphon-working-fluid-filling-ratio projects/supercritical-co2-chiller.md projects/thermosyphon-working-fluid-filling-ratio.md zh/projects/supercritical-co2-chiller.md zh/projects/thermosyphon-working-fluid-filling-ratio.md
git commit -m "Complete the test-setup project import"
```

Expected audit state: 14 imported facilities, 12 imported projects, layouts A=9, B=8, C=9 overall.

---

### Task 11: Remove Pilot Duplicates and Document Editing

**Files:**
- Modify: `scripts/check-setup-renderer.py`
- Modify: `scripts/check-facility-layouts.py`
- Modify: `scripts/check-public-site.py`
- Modify: `docs/how-to-edit.md`
- Delete: `facility-designs.md`
- Delete: `facilities/falling-film-cooling-a.md`
- Delete: `facilities/falling-film-cooling-b.md`
- Delete: `facilities/falling-film-cooling-c.md`

**Interfaces:**
- Consumes: the canonical falling-film route and all three shared templates.
- Produces: one public route per imported subject and editing documentation for future records.

- [ ] **Step 1: Change audits to reject pilot duplicates**

Assert that `/facility-designs/` and all three `falling-film-cooling-{a,b,c}` outputs are absent, are absent from `sitemap.xml`, and are absent from links. Assert the canonical falling-film route remains present and indexable.

- [ ] **Step 2: Run and verify RED**

```powershell
python scripts/check-setup-renderer.py
python scripts/check-facility-layouts.py
```

Expected: duplicate comparison routes still exist.

- [ ] **Step 3: Remove only the four temporary source routes**

Delete the exact files listed above. Do not remove shared A/B/C CSS or canonical routes.

- [ ] **Step 4: Document the import fields**

In `docs/how-to-edit.md`, add one complete example showing `layout`, `source_slides`, `image_fit`, and nested figures with an empty caption permitted when the source supplies none. State that imported projects may omit `student`, while any provided student must match `_data/team.toml`.

- [ ] **Step 5: Rebuild, verify, and commit**

```powershell
julia --project=. -e "using Franklin; optimize()"
python scripts/check-setup-renderer.py
python scripts/check-facility-layouts.py
python scripts/check-test-setup-import.py
python scripts/check-public-site.py
git add scripts/check-setup-renderer.py scripts/check-facility-layouts.py scripts/check-public-site.py docs/how-to-edit.md
git commit -m "Finalize canonical test-setup routes"
```

---

### Task 12: Full Visual and Regression Verification

**Files:**
- Modify only files required by failures found during this task.
- Do not regenerate golden files or unrelated snapshots.

**Interfaces:**
- Consumes: all 26 canonical records, routes, and extracted-figure assets.
- Produces: verified branch state ready for user review, without push or deployment.

- [ ] **Step 1: Run the complete build and static gates**

```powershell
julia --project=. -e "using Franklin; optimize()"
python scripts/check-setup-renderer.py
python scripts/check-test-setup-import.py
python scripts/check-facility-layouts.py
python scripts/check-public-site.py
python scripts/check-partner-strip.py
python scripts/check-profile-layouts.py
python scripts/check-contrast.py
git diff --check
```

Expected: every command exits 0; contrast reports every pair passing WCAG 2.2 AA.

- [ ] **Step 2: Verify no complete source slide was published**

In `scripts/check-test-setup-import.py`, hash every source `Slide1.jpg` through `Slide31.jpg` and every committed file below `_assets/img/test-setups`. Fail if any hashes match. Scan generated HTML for `Slide*.jpg`, source-directory text, and unresolved `{{`/`}}` markers.

- [ ] **Step 3: Run the full computed browser audit**

```powershell
python scripts/shoot.py --measure
```

Expected: `AUDIT CLEAN` with no overflow, undersized controls, type-floor failures, overlong reading measures, or hidden reveal blocks.

- [ ] **Step 4: Capture all 26 pages at desktop width**

Run `scripts/shoot.py` once per canonical English route at 1440 px, light theme, motion off. Build contact sheets grouped by facilities/projects and inspect every page for wrong crops, unreadable labels, missing captions, figure distortion, text clipping, excessive blank space, and accidental slide furniture.

- [ ] **Step 5: Capture responsive/theme representatives**

Capture one facility and one project for each A/B/C layout at 492 px light and 1440 px dark. Confirm the mobile order is title, narrative, figures, captions; technical diagrams remain fully visible; and white technical canvases are intentional in dark theme.

Use browser developer tools for true 320, 360, and 390 px checks on one dense page from each layout. Confirm no horizontal overflow, clipped diagram labels, or unreadable captions; the Edge command-line harness is not evidence below 492 CSS pixels.

- [ ] **Step 6: Verify live local routes**

Start Franklin in a hidden background process:

```powershell
$repoPath = (Resolve-Path '.').Path
Start-Process -FilePath 'julia' -ArgumentList @('--project=.', '-e', '"using Franklin; serve(clear=false)"') -WorkingDirectory $repoPath -WindowStyle Hidden
```

Probe `/facilities/`, `/projects/`, all 26 English routes, and all 26 Chinese routes with `Invoke-WebRequest`. Every route must return 200 without a complete-slide reference.

- [ ] **Step 7: Inspect final Git state and commit verification fixes**

```powershell
git status --short --untracked-files=all
git diff --check
```

Stage only import-related verification fixes, if any, and commit them:

```powershell
git commit -m "Verify complete test-setup import"
```

Do not create an empty commit. Do not push or deploy.
