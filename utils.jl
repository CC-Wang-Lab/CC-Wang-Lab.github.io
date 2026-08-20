using TOML
using Dates
using SHA

# =============================================================================
#  CC Wang Lab — build-time HTML generators
#
#  Every list on this site is generated here from a file in _data/.
#  Nobody edits HTML to add a person, a paper, a news item or a research area.
#
#  Franklin calls a function named `hfun_foo` when a page contains {{foo}}.
#  Arguments arrive as a Vector{String}: {{foo a b}} -> params == ["a", "b"].
# =============================================================================

# ---------------------------------------------------------------------------
#  Data loading, cached for the whole build
# ---------------------------------------------------------------------------

const _DATA = Dict{String,Any}()

"""Read `_data/<name>.toml` once per build and keep it in memory."""
function data(name::AbstractString)
    get!(_DATA, name) do
        path = joinpath(@__DIR__, "_data", name * ".toml")
        isfile(path) || error("missing data file: $path")
        TOML.parsefile(path)
    end
end

# ---------------------------------------------------------------------------
#  Language
# ---------------------------------------------------------------------------

"""Current page language, `"en"` or `"zh"`. Set by `@def lang` in the page."""
function lang()
    l = try
        locvar(:lang)
    catch
        nothing
    end
    l === nothing && (l = try globvar(:lang) catch; nothing end)
    l === nothing && return "en"
    s = String(l)
    return s == "zh" ? "zh" : "en"
end

"""`lang()` as a valid BCP-47 tag for the `<html lang>` attribute."""
hfun_lang_attr() = lang() == "zh" ? "zh-Hant" : "en"

"""Path prefix for the current language: `""` for English, `"/zh"` for Chinese."""
prefix() = lang() == "zh" ? "/zh" : ""

"""
Look up a bilingual field: `pick(d, "title")` returns `d["title_zh"]` on a
Chinese page and `d["title_en"]` otherwise, falling back to English then `""`.
"""
function pick(d::AbstractDict, key::AbstractString)
    suffixed = key * "_" * lang()
    haskey(d, suffixed) && return d[suffixed]
    haskey(d, key * "_en") && return d[key * "_en"]
    haskey(d, key) && return d[key]
    return ""
end

"""
`{{url research}}` -> `/research/` in English, `/zh/research/` in Chinese.
`{{url home}}`     -> `/` or `/zh/`.

Every internal link in a page must use this. Hard-coding `/research/` works in
English and silently throws Chinese readers back onto the English site.
"""
function hfun_url(params::Vector{String})
    length(params) == 1 || error("{{url page}} needs exactly one argument, got $params")
    p = params[1]
    p == "home" && return prefix() * "/"
    return prefix() * "/" * p * "/"
end

"""`{{ui nav people}}` -> the `people_en` / `people_zh` string in ui.toml."""
function hfun_ui(params::Vector{String})
    length(params) == 2 || error("{{ui section key}} needs exactly two arguments, got $params")
    section, key = params
    ui = data("ui")
    haskey(ui, section) || error("ui.toml has no [$section] section")
    return string(pick(ui[section], key))
end

ui(section, key) = string(pick(data("ui")[section], key))

"""An array-valued ui string, e.g. the typed phrases."""
function ui_list(section, key)
    v = pick(data("ui")[section], key)
    return v isa AbstractVector ? String.(v) : String[]
end

first_or_empty(v) = isempty(v) ? "" : String(v[1])

# ---------------------------------------------------------------------------
#  Small helpers
# ---------------------------------------------------------------------------

"""Escape text that is about to be dropped inside an HTML element."""
function esc(s)
    t = string(s)
    t = replace(t, "&" => "&amp;")
    t = replace(t, "<" => "&lt;")
    t = replace(t, ">" => "&gt;")
    t = replace(t, "\"" => "&quot;")
    return t
end

"""A Bootstrap icon span."""
icon(name) = """<i class="bi bi-$(esc(name))" aria-hidden="true"></i>"""

"""Turn a blank-line-separated string into paragraphs."""
function paras(s)
    chunks = filter(!isempty, strip.(split(string(s), "\n\n")))
    return join(["<p>$(esc(c))</p>" for c in chunks], "\n")
end

# ---------------------------------------------------------------------------
#  Cache busting
#
#  GitHub Pages sends `Cache-Control: max-age=600` on every single file and
#  there is no way to change it. Pages reads no `_headers` file, no
#  `.htaccess` and no per-file rule. So a browser holds `/css/style.css` for
#  ten minutes without asking anybody.
#
#  That is what made visitors hard reload. The HTML and the stylesheet expire
#  independently, so a deploy could hand somebody NEW markup painted with the
#  OLD stylesheet, and the page looked broken rather than merely old.
#
#  The fix is to put the file's own content hash in its URL. Change the file
#  and the URL changes, so the browser cannot serve the old copy. Leave the
#  file alone and the URL is identical, so the cache still does its job.
#
#  This covers CSS and JavaScript, which are the files that change on a normal
#  deploy. Fonts, icons and the hero video are deliberately left alone: they
#  change by being replaced with a differently named file, which busts itself.
# ---------------------------------------------------------------------------

const _FINGERPRINT = Dict{String,String}()

"""
    fingerprint(url)

`/css/style.css` -> `/css/style.css?v=1f4c9a2b`, where the tag is the first 8
hex digits of the SHA-1 of the source file. Computed once per build.

The source path is the URL read backwards through Franklin's copy step:
`/css/` came from `_css/`, `/assets/` came from `_assets/`.

A URL that maps to no file is returned unchanged rather than throwing. A
missing asset is already a visible 404, and a build that dies over a cache tag
is worse than one that ships a file without it.
"""
function fingerprint(url::AbstractString)
    get!(_FINGERPRINT, String(url)) do
        src = startswith(url, "/css/")    ? joinpath(@__DIR__, "_css",    url[6:end]) :
              startswith(url, "/assets/") ? joinpath(@__DIR__, "_assets", url[9:end]) : ""
        (isempty(src) || !isfile(src)) && return String(url)
        return string(url, "?v=", bytes2hex(sha1(read(src)))[1:8])
    end
end

"""`{{asset /css/style.css}}` -> the same URL carrying its content hash."""
hfun_asset(params::Vector{String}) = fingerprint(first_or_empty(params))

"""
    {{scripts motion theme-toggle reveal}}

One `<script src="/assets/js/NAME.js?v=HASH"></script>` per name, in the order
given. The order IS the load order, so it is not decoration.

Why a generator and not `{{asset ...}}` written straight into the tag: Franklin
tokenizes `<script ` as the opening of a block it must not touch, and copies
everything up to `</script>` out verbatim. A `{{...}}` inside a script tag
therefore reaches the live site as literal text. A `<link>` has no such
problem, which is why the stylesheet worked and eleven script tags did not.
Measured 2026-08-20, on the first build after the change.
"""
function hfun_scripts(params::Vector{String})
    io = IOBuffer()
    for name in params
        println(io, """<script src="$(fingerprint("/assets/js/" * name * ".js"))"></script>""")
    end
    return String(take!(io))
end

# ---------------------------------------------------------------------------
#  Navigation and language switch
# ---------------------------------------------------------------------------

# The single source of truth for the top navigation AND the footer's link column.
# Add a page here and it appears in both, in both languages.
const NAV = [
    ("home",         "/"),
    ("projects",     "/projects/"),
    ("people",       "/people/"),
    ("publications", "/publications/"),
    ("news",         "/news/"),
]

# Reachable from the footer, not from the top navigation.
const NAV_FOOT = [
    ("about",   "/about/"),
    ("contact", "/contact/"),
]

"""Relative source path of the page being rendered, e.g. `"zh/research.md"`."""
function rpath()
    p = try
        locvar(:fd_rpath)
    catch
        nothing
    end
    p === nothing ? "index.md" : replace(String(p), '\\' => '/')
end

"""
The mirror of the current page in the other language.

`research.md` <-> `zh/research.md`, and `index.md` <-> `zh/index.md`.
Built from the source path so it can never point at a page that does not exist.
"""
function hfun_lang_switch_url()
    p = rpath()
    p = replace(p, r"\.md$" => "")
    if startswith(p, "zh/")
        rest = p[4:end]
        return rest == "index" ? "/" : "/" * rest * "/"
    else
        return p == "index" ? "/zh/" : "/zh/" * p * "/"
    end
end

function hfun_navbar()
    pre = prefix()
    here = "/" * replace(replace(rpath(), r"^zh/" => ""), r"\.md$" => "") * "/"
    here = here == "/index/" ? "/" : here

    items = String[]
    for (key, href) in NAV
        target = pre * href
        active = here == href ? " active" : ""
        aria   = here == href ? """ aria-current="page\"""" : ""
        push!(items, """
        <li class="nav-item">
          <a class="nav-link$(active)"$(aria) href="$(target)">$(esc(ui("nav", key)))</a>
        </li>""")
    end

    home  = pre == "" ? "/" : pre * "/"
    brand = esc(ui("site", "name"))
    tag   = esc(ui("site", "tag"))
    cta   = esc(ui("nav", "cta"))
    other = hfun_lang_switch_url()
    switch = esc(ui("nav", "switch"))
    themelabel = esc(ui("nav", "theme"))

    return """
<header>
  <nav class="navbar navbar-expand-lg fixed-top lab-nav">
    <div class="container-fluid px-lg-4">

      <a href="$(home)" class="navbar-brand d-flex align-items-center gap-2">
        <img src="/assets/img/logo-mark.png" alt="" width="46" height="21" class="brand-mark">
        <span class="brand-text">
          <span class="brand-name">$(brand)</span>
          <span class="brand-tag">$(tag)</span>
        </span>
      </a>

      <button class="navbar-toggler" type="button" data-bs-toggle="collapse"
              data-bs-target="#navMain" aria-controls="navMain"
              aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="navMain">
        <ul class="navbar-nav ms-auto align-items-lg-center">
$(join(items, "\n"))
          <li class="nav-item ms-lg-3 my-2 my-lg-0">
            <a class="btn btn-cta btn-sm" href="$(pre)/contact/">$(cta)</a>
          </li>
          <li class="nav-item ms-lg-2 d-flex align-items-center gap-1">
            <a class="nav-link lang-switch" href="$(other)" hreflang="$(lang() == "zh" ? "en" : "zh-Hant")">$(switch)</a>
            <button class="btn btn-icon" id="themeToggle" type="button"
                    title="$(themelabel)" aria-label="$(themelabel)">
              <i class="bi bi-sun-fill" id="iconLight" aria-hidden="true"></i>
              <i class="bi bi-moon-stars-fill" id="iconDark" aria-hidden="true"></i>
            </button>
          </li>
        </ul>
      </div>

    </div>
  </nav>
</header>
"""
end

# ---------------------------------------------------------------------------
#  Hero
# ---------------------------------------------------------------------------

function hfun_hero()
    pre = prefix()
    phrases = ui_list("hero", "typed")
    # The first phrase is rendered into the HTML so the line is never empty for
    # a screen reader, a crawler, or a visitor with JavaScript off. typed.js
    # takes over only once it runs.
    first_phrase = first_or_empty(phrases)
    json = "[" * join(["\"" * replace(esc(p), "\"" => "&quot;") * "\"" for p in phrases], ",") * "]"
    # The line reserves its room with an invisible copy of the longest phrase,
    # so a long phrase that wraps and a short one that does not cannot move the
    # buttons underneath. `textwidth` counts a CJK glyph as two columns, which
    # is what makes this pick the right phrase on the Chinese pages too.
    longest = isempty(phrases) ? "" : phrases[argmax(textwidth.(phrases))]
    return """
<section class="hero">
  <!-- No `autoplay` attribute on purpose. The browser re-triggers it after a
       script pauses the video, so the pause control could not hold while it
       was there. hero-video.js starts and stops it from the shared motion flag. -->
  <video class="hero-video" muted loop playsinline preload="auto"
         poster="/assets/video/hero-poster.jpg" aria-hidden="true" tabindex="-1">
    <source src="/assets/video/hero-boiling.mp4" type="video/mp4">
  </video>
  <div class="hero-veil"></div>
  <div class="hero-inner container">
    <h1 class="hero-title">$(esc(ui("hero", "title")))</h1>
    <p class="typed-line" id="typedLine" data-phrases='$(json)'>
      <span class="typed-sizer" aria-hidden="true">$(esc(ui("hero", "typed_lead"))) $(esc(longest))</span>
      <span class="typed-run">
        <span class="typed-lead">$(esc(ui("hero", "typed_lead")))</span>
        <span class="typed-text">$(esc(first_phrase))</span><span class="typed-caret" aria-hidden="true"></span>
      </span>
    </p>
    <div class="hero-actions">
      <a class="btn btn-cta btn-lg" href="$(pre)/contact/">$(esc(ui("hero", "cta2")))</a>
      <a class="btn btn-ghost btn-lg" href="$(pre)/#research">$(esc(ui("hero", "cta1")))</a>
    </div>
  </div>
  <!-- Icon AND label swap together. An earlier version swapped only the icon,
       so a paused page showed a play triangle next to the word "Pause". -->
  <button class="motion-toggle" data-motion-toggle type="button" aria-pressed="false">
    <span class="motion-when-running">$(icon("pause-fill")) $(esc(ui("hero", "motion_pause")))</span>
    <span class="motion-when-paused">$(icon("play-fill")) $(esc(ui("hero", "motion_play")))</span>
  </button>
  <p class="hero-caption">$(esc(ui("hero", "caption")))</p>
</section>
"""
end

# ---------------------------------------------------------------------------
#  Numbers band
#
#  Deliberately NOT four bibliometric numbers. Each one tells a different story:
#  scale, industrial demand, technology output, academic authority.
#  "578 papers" is wrong and is not used anywhere — 578 is research OUTPUTS,
#  of which 439 are journal articles.
# ---------------------------------------------------------------------------

function hfun_numbers()
    g(k) = string(globvar(Symbol(k)))
    rows = [
        (g("lab_people"),   ui("numbers", "people")),
        (g("lab_projects"), ui("numbers", "projects")),
        (g("lab_patents"),  ui("numbers", "patents")),
        (g("lab_citations"), ui("numbers", "cites")),
    ]
    cells = join(["""
      <div class="col-6 col-lg-3">
        <div class="stat">
          <span class="stat-num">$(esc(v))</span>
          <span class="stat-label">$(esc(l))</span>
        </div>
      </div>""" for (v, l) in rows], "\n")
    return """
<section class="band-stats">
  <div class="container">
    <div class="row g-3 text-center">
$(cells)
    </div>
  </div>
</section>
"""
end

# ---------------------------------------------------------------------------
#  Research cards
# ---------------------------------------------------------------------------

function hfun_research_cards()
    pre = prefix()
    areas = data("research")["area"]
    used  = Set(String(p["area"]) for p in data("projects")["project"])
    cards = String[]
    for a in areas
        img  = esc(get(a, "image", "/assets/img/projects/placeholder.svg"))
        body = """
          <span class="card-media-img">
            <img src="$(img)" alt="" loading="lazy">
          </span>
          <span class="card-media-body">
            <span class="card-title">$(esc(pick(a, "title")))</span>
            <span class="card-scope">$(esc(pick(a, "scope")))</span>
          </span>"""
        # An area with no project yet is NOT a link. A card that lifts on hover
        # and then goes nowhere reads as a broken page.
        inner = a["id"] in used ?
            """<a class="card-media" href="$(pre)/projects/#$(esc(a["id"]))">$(body)</a>""" :
            """<div class="card-media is-static">$(body)</div>"""
        push!(cards, """      <div class="col-md-6 col-lg-4">
$(inner)
      </div>""")
    end
    return """<div class="row g-4">
$(join(cards, "
"))
</div>"""
end

# ---------------------------------------------------------------------------
#  Capabilities
# ---------------------------------------------------------------------------

function hfun_capabilities()
    groups = data("capabilities")["group"]
    out = join(["""
      <div class="col-md-6">
        <div class="cap-card" id="$(esc(g["id"]))">
          <span class="card-icon">$(icon(g["icon"]))</span>
          <h3 class="card-title">$(esc(pick(g, "title")))</h3>
          <p class="card-scope">$(esc(pick(g, "lead")))</p>
          <ul class="cap-list">
$(join(["            <li>$(esc(it))</li>" for it in pick(g, "items")], "\n"))
          </ul>
        </div>
      </div>""" for g in groups], "\n")
    return """<div class="row g-4">\n$(out)\n</div>"""
end

"""Just the four capability headings and leads, for the home page."""
function hfun_capabilities_brief()
    groups = data("capabilities")["group"]
    out = join(["""
      <div class="col-md-6 col-lg-3">
        <div class="cap-brief">
          <span class="card-icon">$(icon(g["icon"]))</span>
          <h3 class="card-title">$(esc(pick(g, "title")))</h3>
          <p class="card-scope">$(esc(pick(g, "lead")))</p>
        </div>
      </div>""" for g in groups], "\n")
    return """<div class="row g-4">\n$(out)\n</div>"""
end

# ---------------------------------------------------------------------------
#  Partners strip
#
#  A marquee of organizations the lab has worked with. A row renders its LOGO if
#  `logo` points at a file, and its NAME as text otherwise, so the strip is
#  useful before a single logo file has arrived.
#
#  The heading is "Organizations we have worked with", never "Our clients" and
#  never "Trusted by": the first states a fact, the other two imply endorsement,
#  which is what turns a factual reference into a trademark problem.
# ---------------------------------------------------------------------------

function partner_item(o)
    logo = get(o, "logo", "")
    name = esc(pick(o, "name"))
    body = isempty(logo) ?
        """<span class="pt-name">$(name)</span>""" :
        """<img class="pt-logo" src="$(esc(logo))" alt="$(name)" loading="lazy">"""
    return """<li class="pt-item">$(body)</li>"""
end

"""
`{{partner_strip}}` — two independent bands of organisation names and logos.

WHY TWO BANDS AND NOT ONE MARQUEE WITH TWO ROWS
The first version put both rows inside one control, drifting the same way at 30
and 24 px/s, eight pixels apart. Two nearly-equal speeds side by side read as a
shake, not as movement: the eye tracks the difference between the rows, not the
rows. Each row is now a self-contained band with its own arrows, a real gap
between them, and they drift in OPPOSITE directions. A difference of 52 px/s
reads as two separate things, which is what it is.

A negative `data-speed` is the whole of "the other way"; partners.js needs no
second code path for it.
"""
function hfun_partner_strip()
    orgs = data("partners")["org"]
    isempty(orgs) && return ""

    # Items dealt alternately so both bands come out a similar length. Government
    # funders sit alongside the companies, which is what the lab's own collage
    # slide does; the separate "Funded in part by" line it replaced was a second
    # concept for no gain.
    rowa = [o for (i, o) in enumerate(orgs) if isodd(i)]
    rowb = [o for (i, o) in enumerate(orgs) if iseven(i)]

    function band(items, speed, n)
        row = join([partner_item(o) for o in items], "
          ")
        # The list is duplicated and the loop subtracts exactly one copy when the
        # offset passes it, so the wrap is invisible. The copy is hidden from
        # assistive technology so each name is announced once.
        return """
    <div class="pt-band" data-speed="$(speed)">
      <button class="pt-arrow pt-prev" type="button" aria-label="Scroll row $(n) left">$(icon("chevron-left"))</button>
      <div class="pt-viewport">
        <div class="pt-track">
          <ul class="pt-row">
          $(row)
          </ul>
          <ul class="pt-row" aria-hidden="true">
          $(row)
          </ul>
        </div>
      </div>
      <div class="pt-fade pt-fade-l"></div>
      <div class="pt-fade pt-fade-r"></div>
      <button class="pt-arrow pt-next" type="button" aria-label="Scroll row $(n) right">$(icon("chevron-right"))</button>
    </div>"""
    end

    return """
<section class="section partners" id="partners">
  <div class="container">
    <p class="pt-head">$(esc(ui("partners", "head")))</p>
  </div>

  <div class="pt-bands">
$(band(rowa,  26, 1))
$(band(rowb, -26, 2))
  </div>

  <div class="container">
    <p class="pt-note">$(esc(ui("partners", "note")))</p>
  </div>
</section>
"""
end

# ---------------------------------------------------------------------------
#  Sectors — "do these people solve MY kind of problem?"
# ---------------------------------------------------------------------------

function hfun_sectors()
    ss = data("sectors")["sector"]
    cells = join(["""
      <div class="col-md-6 col-lg-3">
        <div class="sector">
          <span class="card-icon">$(icon(s["icon"]))</span>
          <h3 class="card-title">$(esc(pick(s, "name")))</h3>
          <p class="card-scope">$(esc(pick(s, "work")))</p>
        </div>
      </div>""" for s in ss], "\n")
    return """<div class="row g-4">\n$(cells)\n</div>"""
end

# ---------------------------------------------------------------------------
#  Team
#
#  Staleness check: a `status = "current"` row whose `last_verified` is more
#  than 12 months old prints a build warning. Generating a page from a data
#  file does not stop the data going out of date; this does.
# ---------------------------------------------------------------------------

const STALE_AFTER = Day(365)

function people()
    ps = data("team")["person"]
    today = Dates.today()
    for p in ps
        get(p, "status", "current") == "current" || continue
        lv = get(p, "last_verified", nothing)
        lv === nothing && (@warn "team.toml: '$(get(p,"id","?"))' has no last_verified"; continue)
        d = lv isa Date ? lv : Date(string(lv))
        if today - d > STALE_AFTER
            @warn "team.toml: '$(get(p,"id","?"))' last verified $(d), over 12 months ago — confirm they are still in the lab"
        end
    end
    return ps
end

pi_person() = first(filter(p -> get(p, "tier", "") == "pi", people()))

"""Find one person by id, or throw. Used to resolve a project's `student` field."""
function person_by_id(id::AbstractString)
    hit = filter(p -> get(p, "id", "") == id, data("team")["person"])
    isempty(hit) && error("projects.toml refers to student id '$id', which is not in team.toml")
    return first(hit)
end

"""Find one research area by id, or throw. Used to resolve a project's `area` field."""
function area_by_id(id::AbstractString)
    hit = filter(a -> get(a, "id", "") == id, data("research")["area"])
    isempty(hit) && error("projects.toml refers to area id '$id', which is not in research.toml")
    return first(hit)
end

# ---------------------------------------------------------------------------
#  Projects
#
#  One row in projects.toml plus one Markdown page per project. The row carries
#  a `student` id and an `area` id, so a name or a research area is never typed
#  twice and a typo fails the build instead of rendering an empty card.
# ---------------------------------------------------------------------------

"""Projects sorted by `weight`, lowest first."""
function projects()
    ps = copy(data("projects")["project"])
    sort!(ps; by = p -> get(p, "weight", 999))
    return ps
end

"""
One card. `href` is resolved for the current language.

`data-area` is what the filter bar on the Projects page reads. It costs nothing
on the home page, where the same card is reused and nothing filters.

The link opens in a new tab, by request: a visitor reading the grid is browsing,
and a project write-up is a side trip, not a destination. Remove `target` and
`rel` together if that is ever reversed.
"""
function project_card(p)
    person = person_by_id(p["student"])
    area   = area_by_id(p["area"])
    href   = prefix() * "/projects/" * p["id"] * "/"
    return """
      <div class="col-md-6 col-lg-4 pg-item" data-area="$(esc(p["area"]))">
        <a class="card-media" href="$(esc(href))" target="_blank" rel="noopener">
          <span class="card-media-img">
            <img src="$(esc(p["image"]))" alt="" loading="lazy">
          </span>
          <span class="card-media-body">
            <span class="card-badge">$(esc(pick(area, "title")))</span>
            <span class="card-title">$(esc(pick(p, "title")))</span>
            <span class="card-scope">$(esc(pick(p, "lead")))</span>
            <span class="card-by">$(esc(ui("projects", "by"))): $(esc(pick(person, "name")))</span>
          </span>
        </a>
      </div>"""
end

"""
The Projects page: ONE grid, filtered by research area.

WHY THIS IS NOT A SECTION PER AREA
It was, and it read as a single column. With six areas and three projects, every
group held exactly one card, so the layout never got the chance to put two cards
side by side. Grouping is right once each area has several projects; it is wrong
while the lab is filling the page up.

So the areas become a filter bar instead. The grid keeps every project in one
`row`, three across on a wide screen, and a chip narrows it. That keeps the
contract the home page relies on: a research card links to `/projects/#<area-id>`
and `project-filter.js` reads that hash on load and selects the chip.

A chip is only drawn for an area that actually has a project, which is the same
test the home-page cards use to decide whether to be links at all.
"""
function hfun_project_grid()
    ps = projects()
    areas = filter(a -> any(p -> String(p["area"]) == a["id"], ps), data("research")["area"])

    # Order the cards by research area, then by weight inside it. The grid is no
    # longer grouped, but a reader still meets one area before the next.
    rank = Dict(String(a["id"]) => i for (i, a) in enumerate(data("research")["area"]))
    sort!(ps; by = p -> (get(rank, String(p["area"]), 999), get(p, "weight", 999)))

    chips = String["""    <button type="button" class="pg-chip is-active" data-area="all" data-scope="" aria-pressed="true">$(esc(ui("projects", "all")))</button>"""]
    for a in areas
        push!(chips, """    <button type="button" class="pg-chip" data-area="$(esc(a["id"]))" data-scope="$(esc(pick(a, "scope")))" aria-pressed="false">$(esc(pick(a, "title")))</button>""")
    end

    cards = join([project_card(p) for p in ps], "
")

    return """
<div class="project-filter" id="projectFilter" role="group" aria-label="$(esc(ui("projects", "area")))">
$(join(chips, "
"))
</div>
<p class="pg-scope" id="projectScope" aria-live="polite"></p>
<div class="row g-4" id="projectGrid">
$(cards)
</div>"""
end

"""`{{project_featured 3}}` — the first n projects, for the home page."""
function hfun_project_featured(params::Vector{String})
    n = isempty(params) ? 3 : parse(Int, params[1])
    ps = projects()
    return """<div class="row g-4">\n$(join([project_card(p) for p in ps[1:min(n, length(ps))]], "\n"))\n</div>"""
end

"""
`{{project_header}}` on a project page.

The page declares `project = "<id>"` in its front matter; everything shown here
is looked up from that id, so a project page carries no duplicated facts.
"""
function hfun_project_header()
    id = locvar(:project)
    id === nothing && error("this page needs `project = \"<id>\"` in its front matter")
    hit = filter(p -> p["id"] == String(id), projects())
    isempty(hit) && error("no project with id '$(id)' in projects.toml")
    p = first(hit)
    person = person_by_id(p["student"])
    area   = area_by_id(p["area"])
    return """
<header class="page-hd project-hd">
  <div class="container">
    <p class="project-crumb">
      <a href="$(prefix())/projects/">$(esc(ui("projects", "back")))</a>
    </p>
    <span class="card-badge">$(esc(pick(area, "title")))</span>
    <h1>$(esc(pick(p, "title")))</h1>
    <p>$(esc(pick(p, "lead")))</p>
    <p class="project-by">
      <img class="project-by-photo" src="$(esc(get(person, "photo", "/assets/img/team/placeholder.svg")))" alt="">
      <span>
        <strong>$(esc(pick(person, "name")))</strong><br>
        <span class="muted">$(esc(pick(person, "role")))</span>
      </span>
    </p>
  </div>
</header>
<div class="container">
  <figure class="project-hero">
    <img src="$(esc(p["image"]))" alt="">
  </figure>
</div>
"""
end

function hfun_people_pi()
    p = pi_person()
    hon = get(p, "honors_" * lang(), get(p, "honors_en", String[]))
    links = String[]
    haskey(p, "email")   && !isempty(p["email"])   && push!(links, """<a href="mailto:$(esc(p["email"]))">$(icon("envelope")) $(esc(p["email"]))</a>""")
    haskey(p, "scholar") && !isempty(p["scholar"]) && push!(links, """<a href="$(esc(p["scholar"]))" rel="noopener">$(icon("mortarboard")) Google Scholar</a>""")
    haskey(p, "nycu")    && !isempty(p["nycu"])    && push!(links, """<a href="$(esc(p["nycu"]))" rel="noopener">$(icon("building")) NYCU Academic Hub</a>""")
    return """
<div class="pi-block">
  <div class="pi-photo">
    <img src="$(esc(get(p, "photo", "/assets/img/team/placeholder.svg")))" alt="$(esc(pick(p, "name")))">
  </div>
  <div class="pi-body">
    <h2 class="pi-name">$(person_link(p, esc(pick(p, "name"))))</h2>
    <p class="pi-role">$(esc(pick(p, "role")))</p>
    <ul class="pi-honors">
$(join(["      <li>$(esc(h))</li>" for h in hon], "\n"))
    </ul>
    $(paras(pick(p, "bio")))
    <p class="pi-links">$(join(links, " &middot; "))</p>
  </div>
</div>
"""
end

"""Everyone of one tier who is still in the lab, in file order."""
current(tier) = filter(p -> get(p, "tier", "") == tier && get(p, "status", "") == "current", people())

"""
A photo card, for every tier below the PI.

The card is a LINK when that person has written a page, and a plain card when
they have not. See person_page above: nothing is flagged by hand.
"""
function person_card(p)
    body = """
          <img class="person-photo" src="$(esc(get(p, "photo", "/assets/img/team/placeholder.svg")))" alt="$(esc(pick(p, "name")))">
          <h3 class="person-name">$(esc(pick(p, "name")))</h3>
          <p class="person-role">$(esc(pick(p, "role")))</p>
          <p class="person-topic">$(esc(pick(p, "topic")))</p>"""
    inner = person_page(String(get(p, "id", ""))) ?
        """<a class="person-card is-link" href="$(esc(person_href(p["id"])))">$(body)</a>""" :
        """<div class="person-card">$(body)</div>"""
    return """
      <div class="col-sm-6 col-lg-4">
        $(inner)
      </div>"""
end

"""A table row. Used for the alumni page and the index of everyone."""
function person_row(p)
    name = esc(pick(p, "name"))
    return """
    <li class="person-row">
      <span class="person-row-name">$(person_link(p, name))</span>
      <span class="person-row-role">$(esc(pick(p, "role")))</span>
      <span class="person-row-topic">$(esc(pick(p, "topic")))</span>
    </li>"""
end

cards_of(tier) = (ps = current(tier); isempty(ps) ? "" :
    """<div class="row g-4">
$(join([person_card(p) for p in ps], "
"))
</div>""")

rows_of(tier) = (ps = current(tier); isempty(ps) ? "" :
    """<ul class="person-rows">
$(join([person_row(p) for p in ps], "
"))
</ul>""")

hfun_people_leads()    = cards_of("lead")
hfun_people_postdocs() = cards_of("postdoc")
hfun_people_phd()      = cards_of("phd")
hfun_people_msc()      = cards_of("msc")

"""
`{{people_table}}` — every current member of the lab in one table.

The five card sections above it are good for meeting one person. They are poor
for finding one, and with a placeholder silhouette in every card they are also a
very long page. The table is the index: one line each, in tier order, no photo
needed.

Alumni are deliberately absent. They have their own page, and mixing "here now"
with "was here" in a table with no year column would say the wrong thing.
"""
function hfun_people_table()
    ps = vcat((current(t) for t in ("pi", "lead", "postdoc", "phd", "msc"))...)
    isempty(ps) && return ""
    rows = join([person_row(p) for p in ps], "
")
    return """
<ul class="person-rows person-table">
    <li class="person-row person-row-head">
      <span class="person-row-name">$(esc(ui("people", "col_name")))</span>
      <span class="person-row-role">$(esc(ui("people", "col_role")))</span>
      <span class="person-row-topic">$(esc(ui("people", "col_topic")))</span>
    </li>
$(rows)
</ul>"""
end

function hfun_people_alumni()
    as = filter(p -> get(p, "status", "") == "alumni", people())
    isempty(as) && return """<p class="muted">No alumni recorded yet.</p>"""
    byyear = Dict{Int,Vector{Any}}()
    for p in as
        y = Int(get(p, "left_year", 0))
        push!(get!(byyear, y, Any[]), p)
    end
    out = String[]
    for y in sort(collect(keys(byyear)); rev = true)
        rows = join(["""
      <li class="person-row">
        <span class="person-row-name">$(esc(pick(p, "name")))</span>
        <span class="person-row-role">$(esc(pick(p, "role")))</span>
        <span class="person-row-topic">$(esc(pick(p, "topic")))</span>
      </li>""" for p in byyear[y]], "\n")
        push!(out, """<h2 class="year-head">$(y == 0 ? "&mdash;" : string(y))</h2>\n<ul class="person-rows">\n$(rows)\n</ul>""")
    end
    return join(out, "\n")
end

# ---------------------------------------------------------------------------
#  Contact form
#
#  GitHub Pages has no server. A form here therefore either posts to a third
#  party or it builds a mailto: link. `form_endpoint` in config.md decides
#  which, and an empty endpoint is not a broken page - it is the mailto version,
#  which works today with no account anywhere.
# ---------------------------------------------------------------------------

"""One labelled field. `kind` is "text", "email" or "area"."""
function form_field(id, label, hint, kind, required)
    req  = required ? """ <span class="ff-req">$(esc(ui("form", "required")))</span>""" : ""
    star = required ? " required" : ""
    ph   = isempty(hint) ? "" : """ placeholder="$(esc(hint))\""""
    input = kind == "area" ?
        """<textarea id="$(id)" name="$(id)" rows="6"$(ph)$(star)></textarea>""" :
        """<input id="$(id)" name="$(id)" type="$(kind)"$(ph)$(star)>"""
    return """
      <div class="ff">
        <label for="$(id)">$(esc(label))$(req)</label>
        $(input)
      </div>"""
end

"""
`{{contact_form}}` — the form on /contact/.

Three fields: name, email, message. It replaced a prose list headed "What to
put in the first email"; the four things that list asked for are now the
message placeholder, so the guidance survives without becoming four more boxes.
"""
function hfun_contact_form()
    endpoint = try string(globvar(:form_endpoint)) catch; "" end
    key      = try string(globvar(:form_access_key)) catch; "" end
    to       = try string(globvar(:form_to)) catch; "juliahsieh@nycu.edu.tw" end
    live     = !isempty(endpoint)

    # THREE fields. The first version had eight, one per line of the prose list
    # it replaced, and every extra field is a reason not to send. The four
    # things that list asked for are now the message placeholder: they guide
    # without blocking, and somebody who wants to write two lines can.
    fields = join([
        form_field("name",    ui("form", "name"),    "",                         "text",  true),
        form_field("email",   ui("form", "email"),   "",                         "email", true),
        form_field("message", ui("form", "message"), ui("form", "message_hint"), "area",  true),
    ], "
")

    # THE TWO SERVICES DO NOT SHARE FIELD NAMES.
    #
    # Checked against each project's own documentation on 2026-08-20, because
    # getting this wrong fails SILENTLY: the wrong honeypot name is just an
    # ordinary field, so it never blocks a bot and it turns up as junk in the
    # notification email instead.
    #
    #                 Web3Forms            Formspree
    #   key           access_key           - (in the URL)
    #   subject       subject              _subject
    #   honeypot      botcheck (checkbox)  _gotcha (text)
    #   sender name   from_name            -
    #   reply-to      replyto, or auto from a field named `email`
    #
    # Our email field IS named `email`, so replies go to the visitor on both.
    w3 = occursin("web3forms.com", endpoint)
    subj_name = w3 ? "subject" : "_subject"
    trap_name = w3 ? "botcheck" : "_gotcha"

    hidden = String[]
    isempty(key) || push!(hidden, """<input type="hidden" name="access_key" value="$(esc(key))">""")
    push!(hidden, """<input type="hidden" name="$(subj_name)" value="Project inquiry &mdash; CC Wang Lab website">""")
    w3 && push!(hidden, """<input type="hidden" name="from_name" value="CC Wang Lab website">""")

    # The honeypot. A bot fills every field it finds; a person never sees this
    # one. `tabindex="-1"` keeps it out of the keyboard path too. Web3Forms
    # wants a CHECKBOX here, Formspree a text input - not interchangeable.
    push!(hidden, w3 ?
        """<input class="ff-trap" type="checkbox" name="botcheck" tabindex="-1" aria-hidden="true">""" :
        """<input class="ff-trap" type="text" name="_gotcha" tabindex="-1" autocomplete="off" aria-hidden="true">""")

    return """
<form class="contact-form" id="inquiryForm"
      method="POST"
      action="$(esc(live ? endpoint : "mailto:" * to))"
      data-mailto="$(esc(to))"
      data-trap="$(trap_name)"
      data-live="$(live ? "1" : "0")">
$(join(hidden, "\n"))
$(fields)
      <div class="ff-actions">
        <button class="btn btn-cta" type="submit">$(esc(ui("form", "send")))</button>
      </div>
  <p class="ff-status" role="status" aria-live="polite"
     data-sending="$(esc(ui("form", "sending")))"
     data-sent="$(esc(ui("form", "sent")))"
     data-failed="$(esc(ui("form", "failed")))"></p>
</form>
"""
end

# ---------------------------------------------------------------------------
#  A page per person
#
#  Same shape as a project page: one Markdown file per person per language,
#  declaring `person = "<id>"` in its front matter, and everything in the header
#  looked up from team.toml so no fact is typed twice.
#
#  A card or a table row becomes a LINK only when that person's page exists, in
#  that language. Nobody has to remember to set a flag, and a person with no
#  page yet is not a dead end - it is the same test the research cards use to
#  decide whether they link into Projects.
# ---------------------------------------------------------------------------

"""Does this person have a written page, in the language being built?"""
person_page(id) = isfile((lang() == "zh" ? "zh/" : "") * "people/" * String(id) * ".md")

"""The person's URL, resolved for the current language."""
person_href(id) = prefix() * "/people/" * String(id) * "/"

"""Wrap `inner` in a link to the person's page, but only if that page exists."""
function person_link(p, inner)
    id = String(get(p, "id", ""))
    person_page(id) || return inner
    return """<a href="$(esc(person_href(id)))">$(inner)</a>"""
end

"""
Shared by the three generators that build a person page.
"""
function person_links(p)
    links = String[]
    # A raw URL as link text reads badly. Only the email shows its own value,
    # because an address is worth seeing before it is clicked.
    for (k, ico, label) in (("email", "envelope", ""),
                            ("scholar", "mortarboard", "Google Scholar"),
                            ("website", "globe", ui("people", "website")),
                            ("nycu", "building", "NYCU Academic Hub"))
        v = String(get(p, k, ""))
        isempty(v) && continue
        href = k == "email" ? "mailto:" * v : v
        text = isempty(label) ? v : label
        push!(links, """<a class="pi-chip" href="$(esc(href))" rel="noopener">$(icon(ico)) $(esc(text))</a>""")
    end
    return links
end

function this_person()
    id = locvar(:person)
    id === nothing && error("this page needs `person = \"<id>\"` in its front matter")
    return person_by_id(String(id))
end

"""
`{{person_portrait}}` — the LEFT column: the photograph, then the contact links.

The prose written in the Markdown file follows underneath it in the same column.
That order is the whole point of the layout: a reader meets the face, then the
story, and the checkable record sits alongside in the other column.
"""
function hfun_person_portrait()
    p = this_person()
    links = person_links(p)
    return """
<figure class="pi-portrait-frame">
  <img class="pi-portrait" src="$(esc(get(p, "photo", "/assets/img/team/placeholder.svg")))" alt="$(esc(pick(p, "name")))">
</figure>
$(isempty(links) ? "" : """<div class="pi-chips">""" * join(links, "") * "</div>")
"""
end

"""
`{{person_header}}` — the page header band: crumb, eyebrow, name, titles, rule.

The `PI:` prefix is driven by `tier` in team.toml, so it appears on the head of
the laboratory and on nobody else without anyone having to remember.
"""
const TIER_LABEL = Dict(
    "pi"      => "pi_head",
    "lead"    => "lead_head",
    "postdoc" => "postdoc_head",
    "phd"     => "phd_head",
    "msc"     => "msc_head",
)

function hfun_person_header()
    p = this_person()
    tier = String(get(p, "tier", ""))
    # The eyebrow reuses the SAME strings as the section headings on the People
    # page, so a person is described by one word everywhere on the site.
    eyebrow = tier == "pi" ? ui("home", "pi_head") :
              haskey(TIER_LABEL, tier) ? ui("people", TIER_LABEL[tier]) : ""
    topic = String(get(p, "topic_" * lang(), get(p, "topic_en", "")))
    return """
<header class="page-hd person-hd">
  <div class="container">
    <p class="project-crumb">
      <a class="link-arrow" href="$(prefix())/people/"><span class="link-arrow-mark">&larr;</span> $(esc(ui("people", "back")))</a>
    </p>
$(isempty(eyebrow) ? "" : """    <p class="card-badge pi-eyebrow">""" * esc(eyebrow) * "</p>")
    <h1 class="pi-heading">$(esc(pick(p, "name")))</h1>
    <p class="pi-titles">$(esc(pick(p, "role")))$(isempty(topic) ? "" : "<br><span class=\"pi-topic\">" * esc(topic) * "</span>")</p>
    <div class="pi-rule"></div>
  </div>
</header>
"""
end

"""
`{{person_facts}}` — the structured record beside a person's prose.

The shape is how research groups usually present a principal investigator: the
narrative on one side, the checkable facts on the other, each under its own
label. Somebody deciding whether to approach the laboratory reads the right-hand
column; somebody who wants to know what the work is like reads the left.

Every row is OPTIONAL. A person with nothing but a topic renders nothing at all
rather than a table of empty labels, so one page template serves the head of the
laboratory and a first-year student alike.

`interests` is a list of research-area IDS, resolved through area_by_id. The
titles are therefore never typed twice, they come out in the language being
built, and a wrong id stops the build with the id named.
"""
function hfun_person_facts()
    id = locvar(:person)
    id === nothing && return ""
    p = person_by_id(String(id))

    lst(k) = String.(get(p, k * "_" * lang(), get(p, k * "_en", String[])))

    rows = Tuple{String,Vector{String}}[]

    ints = String.(get(p, "interests", String[]))
    isempty(ints) || push!(rows,
        (ui("people", "interests_head"), [esc(pick(area_by_id(i), "title")) for i in ints]))

    for (k, label) in (("positions", "positions_head"),
                       ("education", "education_head"),
                       ("honors",    "awards_head"))
        v = esc.(lst(k))
        isempty(v) || push!(rows, (ui("people", label), v))
    end

    # Projects are a LIST OF LINKS, not a grid of cards. The cards repeated the
    # image and the summary that the project's own page already opens with, and
    # a person page is a record, not a second index. Asked for on 2026-08-20.
    mine = filter(pr -> String(pr["student"]) == String(id), projects())
    isempty(mine) || push!(rows, (ui("people", "projects_head"),
        ["""<a href="$(esc(prefix()))/projects/$(esc(pr["id"]))/">$(esc(pick(pr, "title")))</a>"""
         for pr in mine]))

    isempty(rows) && return ""

    blocks = String[]
    for (label, vals) in rows
        # `vals` may already contain markup (the project links), so the
        # escaping happens where each value is built, not here.
        items = join(["      <li>" * v * "</li>" for v in vals], "\n")
        push!(blocks, """
  <div class="pf-row">
    <div class="pf-label">$(esc(label))</div>
    <ul class="pf-values">
$(items)
    </ul>
  </div>""")
    end

    return """<div class="person-facts">
$(join(blocks, "\n"))
</div>"""
end

# ---------------------------------------------------------------------------
#  Publications
# ---------------------------------------------------------------------------

function hfun_publications()
    d = data("publications")
    themes = d["theme"]
    papers = d["paper"]
    out = String[]
    for t in themes
        ps = filter(p -> p["theme"] == t["id"], papers)
        isempty(ps) && continue
        sort!(ps; by = p -> -Int(p["year"]))
        items = join(["""
      <li class="pub">
        <span class="pub-title">$(esc(p["title"]))</span>
        <span class="pub-meta">$(esc(p["venue"])), $(p["year"])$(haskey(p, "citations") ? " &middot; " * string(p["citations"]) * " citations" : "")</span>
      </li>""" for p in ps], "\n")
        push!(out, """
<section class="pub-theme" id="$(esc(t["id"]))">
  <h2>$(esc(pick(t, "name")))</h2>
  <ol class="pub-list">
$(items)
  </ol>
</section>""")
    end
    return join(out, "\n")
end

# ---------------------------------------------------------------------------
#  News
# ---------------------------------------------------------------------------

function news_items()
    its = copy(data("news")["item"])
    sort!(its; by = i -> i["date"], rev = true)
    return its
end

"""`{{news}}` for all of them, `{{news 3}}` for the newest three."""
function hfun_news(params::Vector{String} = String[])
    its = news_items()
    if !isempty(params)
        n = parse(Int, params[1])
        its = its[1:min(n, length(its))]
    end
    cards = join(["""
      <div class="col-md-4">
        <article class="news-card">
          <p class="news-date">$(Dates.format(i["date"], "d u yyyy"))<span class="news-tag">$(esc(get(i, "tag", "")))</span></p>
          <h3 class="news-title">$(esc(pick(i, "title")))</h3>
          <p class="news-body">$(esc(pick(i, "body")))</p>
        </article>
      </div>""" for i in its], "\n")
    return """<div class="row g-4">\n$(cards)\n</div>"""
end

"""
`{{news_slider}}` — the home page band directly under the hero.

Built to the same pattern as imec.com: the slides CROSS-FADE rather than sliding
sideways, and the navigation underneath is a row of titles, each sitting above a
progress line that fills across the slide's dwell time.

The markup carries no timing. `news-slider.js` owns that, so it can refuse to
auto-advance for a visitor who asked for reduced motion while leaving the arrows
and the title navigation working.
"""
function hfun_news_slider()
    pre = prefix()
    its = news_items()
    isempty(its) && return ""
    n = min(4, length(its))
    its = its[1:n]

    slides = join(["""
        <article class="ns-slide$(k == 1 ? " is-active" : "")" data-index="$(k-1)">
          <p class="ns-date">$(Dates.format(i["date"], "d u yyyy"))<span class="news-tag">$(esc(get(i, "tag", "")))</span></p>
          <h3 class="ns-title">$(esc(pick(i, "title")))</h3>
          <p class="ns-body">$(esc(pick(i, "body")))</p>
        </article>""" for (k, i) in enumerate(its)], "\n")

    navitems = join(["""
        <button class="ns-nav-item$(k == 1 ? " is-active" : "")" type="button" data-goto="$(k-1)">
          <span class="ns-nav-line"><span class="ns-nav-fill"></span></span>
          <span class="ns-nav-title">$(esc(pick(i, "title")))</span>
        </button>""" for (k, i) in enumerate(its)], "\n")

    return """
<section class="news-slider" id="newsSlider" aria-roledescription="carousel"
         aria-label="$(esc(ui("home", "news_head")))">
  <div class="container">
    <p class="ns-head">$(esc(ui("home", "news_head")))</p>

    <div class="ns-stage">
      <button class="ns-arrow ns-prev" type="button" aria-label="Previous">$(icon("chevron-left"))</button>
$(slides)
      <button class="ns-arrow ns-next" type="button" aria-label="Next">$(icon("chevron-right"))</button>
    </div>

    <div class="ns-nav">
$(navitems)
    </div>

    <p class="ns-more"><a class="link-arrow" href="$(pre)/news/">$(esc(ui("home", "news_link"))) <span class="link-arrow-mark">&rarr;</span></a></p>
  </div>
</section>
"""
end

# ---------------------------------------------------------------------------
#  Footer
# ---------------------------------------------------------------------------

function hfun_footer()
    pre = prefix()
    navlinks = join(["""<a href="$(pre)$(href)">$(esc(ui("nav", k)))</a>""" for (k, href) in NAV], "
          ")
    return """
<footer class="lab-foot">
  <div class="container">
    <div class="row g-4">

      <div class="col-lg-5">
        <p class="foot-brand">$(esc(ui("site", "name")))</p>
        <p class="foot-uni">$(esc(ui("site", "uni")))</p>
        <p class="foot-addr">$(esc(ui("foot", "address")))</p>
      </div>

      <div class="col-6 col-lg-3">
        <p class="foot-head">$(esc(ui("foot", "nav")))</p>
        <nav class="foot-nav foot-nav-2col">
          $(navlinks)
          <a href="$(pre)/people/alumni/">$(esc(ui("people", "alumni_link")))</a>
$(join(["""          <a href="$(pre)$(href)">$(esc(ui("nav", k)))</a>""" for (k, href) in NAV_FOOT], "\n"))
        </nav>
      </div>

      <div class="col-6 col-lg-4">
        <p class="foot-head">$(esc(ui("foot", "contact")))</p>
        <nav class="foot-nav">
          <a href="mailto:$(esc(ui("foot", "email")))">$(icon("envelope")) $(esc(ui("foot", "email")))</a>
          <span class="foot-plain">$(icon("telephone")) $(esc(ui("foot", "phone")))</span>
          <a href="$(pre)/contact/">$(icon("geo-alt")) $(esc(ui("foot", "contact")))</a>
        </nav>
      </div>

    </div>

    <hr class="foot-rule">

    <p class="foot-fine">
      &copy; 2026 $(esc(ui("foot", "copy")))
      &nbsp;&middot;&nbsp;
      $(esc(ui("foot", "built")))
      <a href="https://github.com/JuliaDocs/Franklin.jl" rel="noopener">Franklin.jl</a> (MIT).
      <br>
      $(esc(ui("foot", "dev"))) &mdash;
      <a href="mailto:meysam.gholampoor@gmail.com">meysam.gholampoor@gmail.com</a>
    </p>
  </div>
</footer>
"""
end
