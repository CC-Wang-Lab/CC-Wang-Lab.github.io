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

"""A data row is public unless it is explicitly marked as a placeholder."""
is_public(row::AbstractDict) = !Bool(get(row, "placeholder", false))

"""Return only records approved for public rendering, preserving source order."""
public_rows(rows) = filter(is_public, rows)

"""A localized, semantic empty state for a public collection page."""
empty_state(kind::AbstractString) =
    """<p class="empty-state" data-empty-state="$(esc(kind))">$(esc(ui("empty", kind)))</p>"""

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

"""
A number for SVG markup.

Julia prints `120.0` for a whole Float64, and a coordinate reading `120.0` in a
drawing is noise a reviewer has to look past. Whole numbers come out whole;
everything else keeps two decimals, which on a 1200-unit canvas is under half a
pixel at any width this site renders at.
"""
svgnum(x) = (r = round(float(x); digits = 2); isinteger(r) ? string(Int(r)) : string(r))

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
    ("facilities",   "/facilities/"),
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

"""Whether a data-backed navigation destination currently has public content."""
function section_has_public_records(key::AbstractString)
    key == "news"       && return !isempty(public_rows(data("news")["item"]))
    key == "facilities" && return !isempty(public_rows(data("facilities")["item"]))
    key == "people"     && return any(p -> get(p, "status", "current") == "current",
                                       public_rows(data("team")["person"]))
    key == "projects"   && return !isempty(public_rows(data("projects")["project"]))
    return true
end

# Facilities remains discoverable while its records are being prepared. Its
# empty page is still noindex; this exception affects navigation only.
visible_nav() = filter(item -> first(item) == "facilities" ||
                                section_has_public_records(first(item)), NAV)

public_alumni_records() = filter(p -> get(p, "status", "") == "alumni",
                                  public_rows(data("team")["person"]))

function page_noindex()
    explicit = try
        locvar(:noindex)
    catch
        nothing
    end
    explicit === true && return true
    explicit !== nothing && lowercase(string(explicit)) == "true" && return true

    page = replace(rpath(), r"^zh/" => "")
    page == "news.md"          && return !section_has_public_records("news")
    page == "facilities.md"    && return !section_has_public_records("facilities")
    page == "projects.md"      && return !section_has_public_records("projects")
    page == "people.md"        && return !section_has_public_records("people")
    page == "people/alumni.md" && return isempty(public_alumni_records())
    return false
end

hfun_page_robots() = page_noindex() ?
    """<meta name="robots" content="noindex,follow">""" : ""

"""Whether the current Markdown page is backed by one team record."""
function is_person_page()
    id = try
        locvar(:person)
    catch
        nothing
    end
    return id !== nothing && !isempty(String(id))
end

"""Point every profile at its clean public route."""
function hfun_page_canonical()
    is_person_page() || return ""
    id = String(locvar(:person))
    base = try
        string(globvar(:website_url))
    catch
        ""
    end
    isempty(base) && return ""
    href = replace(base, r"/+$" => "") * person_href(id)
    return """<link rel="canonical" href="$(esc(href))">"""
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
    for (key, href) in visible_nav()
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
              aria-expanded="false" aria-label="$(esc(ui("nav", "menu")))">
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
  <div class="hero-motion-row container">
    <button class="motion-toggle" data-motion-toggle type="button" aria-pressed="false">
      <span class="motion-when-running">$(icon("pause-fill")) $(esc(ui("hero", "motion_pause")))</span>
      <span class="motion-when-paused">$(icon("play-fill")) $(esc(ui("hero", "motion_play")))</span>
    </button>
  </div>
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

"""
The picture inside a `.card-media` frame: an inline `<svg>` for a line drawing,
a plain `<img>` for a photograph. The file extension in `_data/` decides, so
swapping a drawing for a real photograph is one line of TOML and nothing else.

WHY AN SVG IS INLINED RATHER THAN LINKED

An SVG loaded through `<img src=...>` is a CLOSED DOCUMENT. Neither the page's
stylesheet nor its scripts can reach inside it, so `stroke-dashoffset` could
never be driven from `style.css` and a drawing could not draw itself. Inlining
is what buys the effect.

It pays for itself twice more. Four fewer HTTP requests on the home page, and no
`fingerprint()` cache tag needed, because the bytes travel inside the HTML and a
new deploy therefore cannot hand anybody a stale drawing.

The art stays in FILES under `_assets/img/research/`, where it is editable and
diffable, and is read once per build. `_ART` is the same module-level cache
`_FINGERPRINT` uses, for the same reason: `index.md` and `zh/index.md` ask for
the same six pictures.

WHAT IS STRIPPED ON THE WAY THROUGH

The comment header. Every one of those files opens with an explanation of the
four rules it obeys, which is worth a lot to the next person editing it and
nothing at all to a visitor. Four of them would put about 4 kB of prose on the
home page. The comments stay in the repository and never reach the wire.

AN SVG HAS TO OPT IN, BY CARRYING class="card-art"

Not every `.svg` under `_assets/` wants inlining. `projects/placeholder.svg` is
the one that proved it: it carries `role="img"` and an `aria-label`, which are
right for a file loaded through `<img>` and wrong once the same markup is part
of the page, because a screen reader then announces "No image yet" on a card
whose title has already said what it is. It also hard-codes its colours, so it
would not follow the dark theme.

So inlining is not decided by the extension alone. A file opts in by being card
art, and the ones that do carry `aria-hidden="true"` and no colour. Everything
else keeps the `<img>` it always had.

A path that is not an opted-in `.svg`, or one that is not on disk, falls back to
`<img>`. A missing picture is already a visible 404. A build that dies over one
is worse. Same call as `fingerprint()` makes.
"""
const _ART = Dict{String,String}()

function card_media_art(path)
    url = String(path)
    if endswith(lowercase(url), ".svg") && startswith(url, "/assets/")
        src = joinpath(@__DIR__, "_assets", url[9:end])
        if isfile(src) && occursin("class=\"card-art\"", read(src, String))
            return get!(_ART, url) do
                art = read(src, String)
                art = replace(art, r"<!--.*?-->"s => "")
                # Collapse to one line. Every `d` attribute in these files is
                # written on a single line, so nothing inside a path can be
                # joined to its neighbour by this.
                return join(strip.(split(art, '\n')), "")
            end
        end
    end
    return """<img src="$(esc(url))" alt="" loading="lazy">"""
end

function hfun_research_cards()
    pre = prefix()
    areas = data("research")["area"]
    used  = Set(String(p["area"]) for p in projects())
    cards = String[]
    for a in areas
        art  = card_media_art(get(a, "image", "/assets/img/projects/placeholder.svg"))
        body = """
          <span class="card-media-img">
            $(art)
          </span>
          <span class="card-media-body">
            <span class="card-title">$(esc(pick(a, "title")))</span>
            <span class="card-scope">$(esc(pick(a, "scope")))</span>
          </span>"""
        # An area with no project yet is NOT a link, and says so with
        # `is-static`: the cursor stays an arrow. It still lifts on hover like
        # every other card, because a row where half the cards answer the mouse
        # and half ignore it reads as a broken page. See .card-media.is-static
        # in style.css; nothing about the motion is decided here.
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
#  Heat path
#
#  NOT CALLED BY ANY PAGE YET. It was built for the laboratory-head slot on the
#  home page, it builds clean and both gates pass, and then it was parked for a
#  look first. Preview it by opening _internal-docs/preview/heat-path.html;
#  how-to-switch-it-on.md beside it carries the one markup block that turns it
#  on, and the list of what to delete if the answer is no.
#
#  One pipe, one station per research area, dots travelling from the hot end to
#  the cold end. It answers the question the research cards do not: what ORDER
#  does this work happen in.
#
#  TWO THINGS ARE EMITTED, NOT ONE, AND THAT SPLIT IS THE WHOLE DESIGN
#
#  1. An <svg> carrying ONLY geometry: two pipe walls, an inlet tick, the
#     flowing fluid, an outlet arrow and one ring per station.
#
#     No TEXT, because SVG text does not obey the 12.8px floor that
#     `scripts/shoot.py --measure` enforces. A 16-unit label on a 1200-unit
#     canvas renders at 4.6px on a phone, and getComputedStyle still reports the
#     unscaled 16px, so NOTHING in the toolchain would catch it.
#
#     No ICONS, because Bootstrap Icons is a webfont here and the glyph arrives
#     through `.bi-cpu::before`. ::before does not exist on an SVG element in
#     any browser. The icons therefore live in the list below, in the same
#     .card-icon tile the rest of the site uses, at a real font size.
#
#  2. An <ol> underneath carrying the icon, the title and the note. Everything
#     readable is there, translated from _data/heatpath.toml like every other
#     list on this site. An ORDERED list, because the order IS the point, and
#     because that is the accessible form of "a path" - which is also why the
#     SVG is aria-hidden rather than role="img". It holds nothing the list does
#     not already say, and a <title> would make a screen reader announce all
#     five stations twice.
#
#  THE ALIGNMENT CONTRACT, WHICH IS NOT NEGOTIABLE
#
#  Station i sits at x = W(2i-1)/2n, the centre of the i-th of n EQUAL columns.
#  The list underneath must therefore be n equal columns with NO gutter between
#  them, the breathing room living as padding INSIDE each cell. A Bootstrap
#  `row g-4` will NOT do: its negative outer margins make it 1.5rem wider than
#  the container, which slides the first and last labels about 10px off their
#  own nodes at every width. A CSS grid with `gap` misses by 0.4 x gap for the
#  same reason. See .hp-stops in _css/style.css.
# ---------------------------------------------------------------------------

"""
`{{heat_path}}` - the animated heat-path diagram on the home page.

Geometry is derived from the number of `[[stop]]` rows, so adding a sixth
station needs no CSS and no change here.

A station LINKS to `/projects/#<area-id>` when that area has a project and is a
plain block when it does not. Same rule and same reason as `hfun_research_cards`
above: a block that answers the mouse and then goes nowhere reads as broken.

Every `url(#hpGrad)` below is a presentation ATTRIBUTE and not a stylesheet
rule, on purpose. A `url()` written in an external stylesheet resolves its
fragment against the STYLESHEET's own URL in some engines, and
`/css/style.css?v=...#hpGrad` does not exist. The reverse also holds, which is
why `stop-color`, `fill` and `stroke-width` are in the stylesheet instead: a
presentation attribute cannot take `var()`, so a colour token could never reach
one. A presentation attribute loses to any author rule, so the two halves never
collide.
"""
function hfun_heat_path()
    pre   = prefix()
    stops = data("heatpath")["stop"]
    n     = length(stops)
    n >= 2 || error("heatpath.toml needs at least two [[stop]] rows, found $(n)")

    # Checked HERE and not by area_by_id, whose message names projects.toml and
    # would send the next person to the wrong file entirely.
    known = Set(String(a["id"]) for a in data("research")["area"])
    for s in stops
        String(get(s, "area", "")) in known || error(
            "heatpath.toml: stop '$(get(s, "id", "?"))' has area = " *
            "'$(get(s, "area", ""))', which is not an id in research.toml")
    end
    used = Set(String(p["area"]) for p in projects())

    # --- geometry, all in viewBox units --------------------------------------
    W, H = 1200, 120     # 120, not 200: at 1296px wide a 6:1 box would be 216px
    Y    = 60            # tall with 170 of that empty. A pipe is long and thin.
    X0   = 24            # inlet, a little before the first station
    X1   = W - X0        # the point of the outlet arrow
    TIP  = 30            # length of the arrowhead
    BORE = 12            # half the bore; the two walls sit at Y +/- BORE
    RING, CORE = 15, 5   # station ring, and its filled core

    # The centre of column i of n equal columns. This is the contract.
    xs = [W * (2i - 1) / (2n) for i in 1:n]

    nodes = join(["""
    <circle class="hp-ring" cx="$(svgnum(x))" cy="$(Y)" r="$(RING)" stroke="url(#hpGrad)"/>
    <circle class="hp-core" cx="$(svgnum(x))" cy="$(Y)" r="$(CORE)" fill="url(#hpGrad)"/>"""
    for x in xs], "\n")

    # gradientUnits="userSpaceOnUse" is REQUIRED, not stylistic: a horizontal
    # line has a zero-HEIGHT bounding box, and the objectBoundingBox default
    # degenerates on it. It also means every element painting with #hpGrad picks
    # up the colour belonging to its own x, so station 1's ring comes out hot
    # and station 5's cool from one gradient, with no second definition.
    svg = """
  <svg class="hp-figure" viewBox="0 0 $(W) $(H)" aria-hidden="true" focusable="false">
    <defs>
      <linearGradient id="hpGrad" gradientUnits="userSpaceOnUse"
                      x1="$(X0)" y1="0" x2="$(X1)" y2="0">
        <stop class="hp-hot" offset="0"/>
        <stop class="hp-cool" offset="1"/>
      </linearGradient>
    </defs>
    <path class="hp-wall" d="M $(X0) $(Y - BORE) H $(X1 - TIP) M $(X0) $(Y + BORE) H $(X1 - TIP)"/>
    <path class="hp-inlet" d="M $(X0) $(Y - BORE - 6) V $(Y + BORE + 6)" stroke="url(#hpGrad)"/>
    <path class="hp-flow" d="M $(X0) $(Y) H $(X1 - TIP - 6)" stroke="url(#hpGrad)"/>
    <path class="hp-tip" d="M $(X1) $(Y) L $(X1 - TIP) $(Y - BORE - 4) L $(X1 - TIP) $(Y + BORE + 4) Z" fill="url(#hpGrad)"/>
$(nodes)
  </svg>"""

    cells = String[]
    for s in stops
        aid  = String(s["area"])
        body = """
          <span class="card-icon">$(icon(s["icon"]))</span>
          <h3 class="card-title">$(esc(pick(s, "title")))</h3>
          <p class="card-scope">$(esc(pick(s, "note")))</p>"""
        inner = aid in used ?
            """<a class="hp-link" href="$(pre)/projects/#$(esc(aid))">$(body)
        </a>""" :
            """<div class="hp-body">$(body)
        </div>"""
        push!(cells, """      <li class="hp-stop" data-area="$(esc(aid))">
        $(inner)
      </li>""")
    end

    # role="list" is explicit because .hp-stops sets list-style:none, and
    # Safari/VoiceOver drops list semantics the moment it sees that.
    return """
<figure class="hp" data-stops="$(n)">
$(svg)
  <ol class="hp-stops" role="list">
$(join(cells, "\n"))
  </ol>
</figure>"""
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
        """<img class="pt-logo" src="$(esc(logo))" alt="$(name)" loading="lazy" draggable="false">"""
    return """<li class="pt-item">$(body)</li>"""
end

"""
`{{partner_strip}}` — two independent bands of organisation names and logos.

WHY TWO BANDS AND NOT ONE MARQUEE WITH TWO ROWS
The first version put both rows inside one control, drifting the same way at 30
and 24 px/s, eight pixels apart. Two nearly-equal speeds side by side read as a
shake, not as movement: the eye tracks the difference between the rows, not the
rows. Each row is now a self-contained, named control with a real gap between
them, and they drift in OPPOSITE directions. A difference of 52 px/s reads as
two separate things, which is what it is.

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

    function band(items, speed, row_number)
        row = join([partner_item(o) for o in items], "
          ")
        label = ui("partners", row_number == 1 ? "row_one" : "row_two")
        # The list is duplicated and the loop subtracts exactly one copy when the
        # offset passes it, so the wrap is invisible. The copy is hidden from
        # assistive technology so each name is announced once.
        return """
    <div class="pt-band" data-speed="$(speed)" data-partner-row="$(row_number)">
      <div class="pt-viewport" tabindex="0" role="group"
           aria-label="$(esc(label))" aria-describedby="partners-instructions"
           aria-keyshortcuts="ArrowLeft ArrowRight">
        <div class="pt-track">
          <ul class="pt-row">
          $(row)
          </ul>
          <ul class="pt-row" aria-hidden="true">
          $(row)
          </ul>
        </div>
      </div>
      <div class="pt-fade pt-fade-l" aria-hidden="true"></div>
      <div class="pt-fade pt-fade-r" aria-hidden="true"></div>
    </div>"""
    end

    return """
<section class="section partners" id="partners">
  <div class="container">
    <p class="pt-head">$(esc(ui("partners", "head")))</p>
    <p class="visually-hidden" id="partners-instructions">$(esc(ui("partners", "instructions")))</p>
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
#  Facilities — the equipment underneath the capabilities.
#
#  The SAME card as a project card, on purpose: image, research area, title,
#  one line of scope. Each public facility has one canonical detail page, so
#  the card is an ordinary link.
# ---------------------------------------------------------------------------

"""
`{{facilities}}` — the equipment grid at /facilities/.

`area` is optional and is an id from research.toml, so the badge is bilingual
for free and a typo stops the build. `image` is optional too and falls back to
the shared placeholder, which is what every other card on this site does.
"""
function hfun_facilities()
    facilities = facility_items()
    isempty(facilities) && return empty_state("facilities")
    cards = String[]
    for f in facilities
        href = prefix() * "/facilities/" * String(f["id"]) * "/"
        badge = haskey(f, "area") ? """
            <span class="card-badge">$(esc(pick(area_by_id(String(f["area"]), "facilities.toml"), "title")))</span>""" : ""
        img = esc(get(f, "image", "/assets/img/projects/placeholder.svg"))
        image_fit = lowercase(String(get(f, "image_fit", "cover")))
        image_fit in ("cover", "contain") ||
            error("facilities.toml: image_fit for '$(f["id"])' must be cover or contain")
        image_class = image_fit == "contain" ? " card-media-img--contain" : ""
        push!(cards, """
      <div class="col-md-6 col-lg-4">
        <a class="card-media" id="$(esc(f["id"]))" href="$(esc(href))">
          <span class="card-media-img$(image_class)">
            <img src="$(img)" alt="" loading="lazy">
          </span>
          <span class="card-media-body">$(badge)
            <span class="card-title">$(esc(pick(f, "title")))</span>
            <span class="card-scope">$(esc(pick(f, "lead")))</span>
          </span>
        </a>
      </div>""")
    end
    return """<div class="row g-4">\n$(join(cards, "\n"))\n</div>"""
end

facility_items() = public_rows(data("facilities")["item"])

function facility_by_id(id::AbstractString)
    hit = filter(f -> get(f, "id", "") == id, facility_items())
    isempty(hit) && error("no public facility with id '$(id)' in facilities.toml")
    return first(hit)
end

function render_setup_item(item)::String
    item isa AbstractDict || return "<li>$(esc(string(item)))</li>"

    item_type = String(get(item, "type", ""))
    item_type == "source-url" ||
        error("unsupported structured section item type '$item_type'")
    label = strip(pick(item, "label"))
    isempty(label) && error("source-url section item needs a label")
    value = strip(String(get(item, "value", "")))
    occursin(r"^https://[^/?#\s]+(?:[/?#][^\s]*)?$", value) ||
        error("source-url section item needs an absolute https:// value")
    safe_value = esc(value)
    return "<li>$(esc(label)) <a href=\"$(safe_value)\">$(safe_value)</a></li>"
end

function render_setup_sections(record::AbstractDict)
    blocks = String[]
    for section in get(record, "section", Any[])
        heading = strip(pick(section, "heading"))
        body = strip(pick(section, "body"))
        items_key = "items_" * lang()
        items = get(section, items_key, get(section, "items_en", Any[]))
        items isa AbstractVector || error("section '$items_key' must be an array")
        any(item -> isempty(strip(string(item))), items) &&
            error("section '$items_key' must not contain blank items")
        heading_html = isempty(heading) ? "" : "<h2>$(esc(heading))</h2>"
        body_html = isempty(body) ? "" : "<p>$(esc(body))</p>"
        items_html = isempty(items) ? "" :
            "<ul>" * join([render_setup_item(item) for item in items]) * "</ul>"
        push!(blocks, "<section>$(heading_html)$(body_html)$(items_html)</section>")
    end
    return join(blocks, "\n")
end

# ---------------------------------------------------------------------------
#  Per-page composition: JUSTIFIED ROWS
#
#  A shared three-layout renderer cannot lay out these pages, because the thing
#  that decides the layout is what the pictures ARE. One record is four
#  micrographs of one comparison set; the next is a rack photograph beside a
#  dot grid 497px wide and 1600px tall. No stylesheet can tell those apart.
#
#  So each page composes itself, in its own front matter:
#
#      blocks = [
#        "row:test-rig",
#        "notes",
#        "row:sintered additively-manufactured",
#        "row:diamond acid-etched",
#      ]
#
#  WHY FRONT MATTER AND NOT `{{figrow a b}}` IN THE BODY, which is what the
#  approved plan said. An unknown hfun name does not throw. Franklin logs a
#  warning and substitutes an empty string, so `{{figrpw a b}}` builds green
#  with two pictures missing and no `{{ }}` left in the HTML for a gate to
#  grep. That is the same silent-no-op class of fault that put 25 of 26
#  records into the wrong grid, and it is the fault this whole pass exists to
#  remove. A front-matter list cannot misspell a function name, because there
#  is no function name in it, and every id in it is checked below.
#
#  THE ARITHMETIC. Each figure is a flex item with `flex: aspect 1 0`. With a
#  zero basis the free space is shared out in proportion to flex-grow, so
#
#      width_i = (W - gaps) * a_i / sum(a)     and     height_i = width_i / a_i
#              = (W - gaps) / sum(a)           the SAME for every item.
#
#  The row therefore fills its container exactly, with nothing cropped and no
#  ragged bottom edge, whatever shapes are in it.
#
#  THE CAP. An image must never be painted wider than its own pixels. Slot
#  width is a_i * h, so the no-upscale condition a_i * h <= w_i reduces to
#  h <= h_i: the row height cap is min(natural height) over the row. It is
#  emitted as `--nat-h` and applied to the row's max-width, never to the
#  image's max-height. Capping the image letterboxes it inside a slot that is
#  still the old size, which breaks the equal-height property the row is for.
# ---------------------------------------------------------------------------

function figure_by_id(record::AbstractDict, id::AbstractString)
    hit = filter(f -> String(get(f, "id", "")) == id, get(record, "figure", Any[]))
    isempty(hit) && error("record '$(record["id"])' has no figure '$(id)'")
    return first(hit)
end

"""One figure inside a justified row."""
function render_fig(figure::AbstractDict)::String
    kind = esc(String(get(figure, "kind", "figure")))
    image = esc(String(figure["image"]))
    haskey(figure, "w") && haskey(figure, "h") ||
        error("figure '$(figure["id"])' has no w/h; run scripts/add-figure-sizes.py")
    w = Int(figure["w"])
    h = Int(figure["h"])
    caption = esc(pick(figure, "caption"))
    caption_html = isempty(caption) ? "" : "\n    <figcaption>$(caption)</figcaption>"
    # --ar-w and --ar-h are the raw integers, never a rounded ratio. Three or
    # more items in one row accumulate the rounding error, and the row then
    # misses its container by a pixel or two at the right-hand edge.
    return """
  <figure class="fig fig--$(kind)" style="--ar-w:$(w);--ar-h:$(h);--nat-w:$(w)px">
    <a class="fig-media" href="$(image)" aria-label="$(esc(ui("figure", "zoom")))"><img src="$(image)" alt="" width="$(w)" height="$(h)" loading="lazy" decoding="async"><span class="fig-zoom" aria-hidden="true"></span></a>$(caption_html)
  </figure>"""
end

"""One justified row of figures, from a list of figure ids."""
function render_fig_row(record::AbstractDict, ids::Vector{String})::String
    isempty(ids) && error("record '$(record["id"])': a row needs at least one figure id")
    figures = [figure_by_id(record, id) for id in ids]
    n = length(figures)
    sum_ar = sum(Int(f["w"]) / Int(f["h"]) for f in figures)
    nat_h = minimum(Int(f["h"]) for f in figures)
    body = join([render_fig(f) for f in figures], "\n")
    return """
<div class="fig-row fig-row--n$(n)" style="--sum-ar:$(round(sum_ar, digits=6));--nat-h:$(nat_h)px;--n:$(n)">
$(body)
</div>"""
end

"""The record's lead paragraph, on its own."""
function render_lead(record::AbstractDict)::String
    lead = esc(pick(record, "body"))
    # Not unconditional. Five records have an empty body_en, and an empty <p>
    # still occupies a line box plus its own bottom margin, so those pages
    # opened on a blank gap nobody could see the cause of.
    isempty(strip(lead)) && return ""
    return """<div class="setup-notes prose"><p>$(lead)</p></div>"""
end

"""One section of the record's words, by its 1-based position."""
function render_section(record::AbstractDict, n::Int)::String
    sections = get(record, "section", Any[])
    1 <= n <= length(sections) ||
        error("record '$(record["id"])': sec:$(n) asked for, but it has $(length(sections)) section(s)")
    one = Dict{String,Any}("section" => Any[sections[n]])
    return """<div class="setup-notes prose">$(render_setup_sections(one))</div>"""
end

"""The record's words: the lead paragraph and every section under it."""
function render_notes(record::AbstractDict)::String
    lead = esc(pick(record, "body"))
    lead_html = isempty(strip(lead)) ? "" : "<p>$(lead)</p>"
    return """<div class="setup-notes prose">$(lead_html)
$(render_setup_sections(record))</div>"""
end

"""Notes beside one figure. Side by side from 992px up, stacked below it."""
function render_split(record::AbstractDict, id::AbstractString)::String
    # A portrait hero is capped at 40rem tall, so it is narrow, and a column
    # sized for a landscape photograph leaves it floating in the middle of
    # white space. Measured on thermal-fin-natural-convection-chamber: 360px
    # of photograph inside a 733px column. A tall hero gets a column that
    # hugs it instead, and the words take everything else.
    figure = figure_by_id(record, id)
    tall = Int(figure["w"]) < Int(figure["h"]) ? " setup-split--tall" : ""
    return """
<div class="setup-split$(tall)">
$(render_notes(record))
$(render_fig_row(record, String[id]))
</div>"""
end

"""Crumb, area badge and title. Shared by the composed and the a/b/c path."""
function setup_header_html(record::AbstractDict, kind::AbstractString)::String
    src = kind == "facility" ? "facilities.toml" : "projects.toml"
    back_path = kind == "facility" ? "/facilities/" : "/projects/"
    back_html = kind == "facility" ?
        "&larr; " * esc(ui("nav", "facilities")) : esc(ui("projects", "back"))
    area = area_by_id(String(record["area"]), src)
    return """
<header class="page-hd setup-study-hd"><div class="container">
  <p class="project-crumb"><a href="$(prefix())$(back_path)">$(back_html)</a></p>
  <span class="card-badge">$(esc(pick(area, "title")))</span>
  <h1>$(esc(pick(record, "title")))</h1>
</div></header>"""
end

"""
Read `blocks` from the front matter and check it against the record.

Every one of these fires on a real mistake somebody can make while composing:
a figure left out, a figure used twice, an id that does not exist, notes put
on a record that has none, or a record with words and nowhere to put them.
"""
function setup_blocks(record::AbstractDict)
    raw = locvar(:blocks)
    raw === nothing && return nothing
    raw isa AbstractVector ||
        error("`blocks` in the front matter must be a list of strings")

    n_sections = length(get(record, "section", Any[]))
    has_lead = !isempty(strip(pick(record, "body")))

    parsed = Tuple{String,Vector{String}}[]
    used = String[]
    lead_blocks = 0
    section_blocks = zeros(Int, n_sections)
    for entry in raw
        text = strip(String(entry))
        if text == "notes"
            # "notes" stands for the lead AND every section, so it counts as
            # placing whatever the record actually has. A record with no lead
            # is not made to say so.
            lead_blocks += has_lead ? 1 : 0
            section_blocks .+= 1
            push!(parsed, ("notes", String[]))
        elseif text == "lead"
            lead_blocks += 1
            push!(parsed, ("lead", String[]))
        elseif startswith(text, "sec:")
            n = tryparse(Int, strip(text[5:end]))
            n === nothing && error("record '$(record["id"])': $(repr(text)) needs a section number")
            1 <= n <= n_sections ||
                error("record '$(record["id"])': $(repr(text)) but it has $(n_sections) section(s)")
            section_blocks[n] += 1
            push!(parsed, ("sec", String[string(n)]))
        elseif startswith(text, "split:")
            lead_blocks += has_lead ? 1 : 0
            section_blocks .+= 1
            ids = String.(split(strip(text[7:end])))
            length(ids) == 1 ||
                error("record '$(record["id"])': split takes exactly one figure id, got $(repr(text))")
            append!(used, ids)
            push!(parsed, ("split", ids))
        elseif startswith(text, "row:")
            ids = String.(split(strip(text[5:end])))
            isempty(ids) && error("record '$(record["id"])': empty row block")
            append!(used, ids)
            push!(parsed, ("row", ids))
        else
            error("record '$(record["id"])': unknown block $(repr(text)); use " *
                  "notes, lead, sec:<n>, split:<figure-id> or row:<figure-id> ...")
        end
    end

    all_ids = [String(f["id"]) for f in get(record, "figure", Any[])]
    for id in used
        id in all_ids ||
            error("record '$(record["id"])': a block names figure '$(id)', which it has not got")
    end
    for id in all_ids
        count(==(id), used) == 1 ||
            error("record '$(record["id"])': figure '$(id)' appears $(count(==(id), used)) times in blocks; it must appear exactly once")
    end
    # Every piece of the record's words is placed exactly once. A lead left
    # out, a section named twice, or a heading placed on a record that has no
    # such section all stop the build here rather than quietly disappearing.
    want_lead = has_lead ? 1 : 0
    lead_blocks == want_lead ||
        error("record '$(record["id"])': the lead paragraph is placed $(lead_blocks) time(s), " *
              "and it must be placed $(want_lead)")
    for (n, count) in enumerate(section_blocks)
        count == 1 ||
            error("record '$(record["id"])': section $(n) is placed $(count) time(s) in blocks; " *
                  "it must be placed exactly once")
    end
    return parsed
end

"""A composed page: header, then the blocks in the order the page asked for."""
function render_setup_rows(record::AbstractDict, kind::AbstractString, blocks)::String
    parts = String[]
    for (name, ids) in blocks
        if name == "notes"
            push!(parts, render_notes(record))
        elseif name == "lead"
            push!(parts, render_lead(record))
        elseif name == "sec"
            push!(parts, render_section(record, parse(Int, ids[1])))
        elseif name == "split"
            push!(parts, render_split(record, ids[1]))
        else
            push!(parts, render_fig_row(record, ids))
        end
    end
    # The first picture is the LCP element on nearly every one of these pages
    # once the notes stop filling a column beside it, and every <img> the site
    # emits is lazy. A lazy LCP image is half a second of empty box.
    body = replace(join(parts, "\n"), "loading=\"lazy\"" => "loading=\"eager\" fetchpriority=\"high\"", count = 1)
    return """
$(setup_header_html(record, kind))
<div class="page-body setup-study-page"><div class="container">
  <div class="setup-rows">
$(body)
  </div>
</div></div>"""
end

"""`{{facility_page}}` — one facility, composed by its own page."""
function hfun_facility_page()::String
    id = locvar(:facility)
    id === nothing && error("this page needs `facility = \"<id>\"` in its front matter")
    record = facility_by_id(String(id))
    blocks = setup_blocks(record)
    blocks === nothing &&
        error("facilities/$(id).md has no `blocks`; every detail page composes itself")
    return render_setup_rows(record, "facility", blocks)
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
    ps = public_rows(data("team")["person"])
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

function pi_person()
    ps = filter(p -> get(p, "tier", "") == "pi", people())
    return isempty(ps) ? nothing : first(ps)
end

"""Find one person by id, or throw. Used to resolve a project's `student` field."""
function person_by_id(id::AbstractString)
    hit = filter(p -> get(p, "id", "") == id, data("team")["person"])
    isempty(hit) && error("projects.toml refers to student id '$id', which is not in team.toml")
    return first(hit)
end

"""Find one research area by id, or throw. Used to resolve a project's `area` field."""
function area_by_id(id::AbstractString, src::AbstractString = "projects.toml")
    hit = filter(a -> get(a, "id", "") == id, data("research")["area"])
    isempty(hit) && error("$src refers to area id '$id', which is not in research.toml")
    return first(hit)
end

# ---------------------------------------------------------------------------
#  Projects
#
#  Projects may carry a `student` id and always carry an `area` id, so a name
#  or research area is never typed twice. An explicit typo still fails the
#  build, while imported lab-owned work can omit `student` and its byline.
# ---------------------------------------------------------------------------

"""Projects sorted by `weight`, lowest first."""
function projects()
    ps = copy(public_rows(data("projects")["project"]))
    sort!(ps; by = p -> get(p, "weight", 999))
    return ps
end

function project_person(project)
    id = get(project, "student", nothing)
    id === nothing && return nothing
    person = person_by_id(String(id))
    return is_public(person) ? person : nothing
end

"""`{{project_setup_page}}` — one imported project, composed by its own page."""
function hfun_project_setup_page()::String
    id = locvar(:project)
    id === nothing && error("this page needs `project = \"<id>\"` in its front matter")
    hit = filter(p -> p["id"] == String(id), projects())
    isempty(hit) && error("no project with id '$(id)' in projects.toml")
    record = first(hit)
    blocks = setup_blocks(record)
    blocks === nothing &&
        error("projects/$(id).md has no `blocks`; every detail page composes itself")
    return render_setup_rows(record, "project", blocks)
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
    person = project_person(p)
    area   = area_by_id(p["area"])
    href   = prefix() * "/projects/" * p["id"] * "/"
    byline = person === nothing ? "" :
        """<span class="card-by">$(esc(ui("projects", "by"))): $(esc(pick(person, "name")))</span>"""
    return """
      <div class="col-md-6 col-lg-4 pg-item" data-area="$(esc(p["area"]))">
        <a class="card-media" href="$(esc(href))" target="_blank" rel="noopener">
          <span class="card-media-img">
            $(card_media_art(p["image"]))
          </span>
          <span class="card-media-body">
            <span class="card-badge">$(esc(pick(area, "title")))</span>
            <span class="card-title">$(esc(pick(p, "title")))</span>
            <span class="card-scope">$(esc(pick(p, "lead")))</span>
            $(byline)
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
    isempty(ps) && return empty_state("projects")
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
    person = project_person(p)
    area   = area_by_id(p["area"])
    byline = person === nothing ? "" : """
    <p class="project-by">
      <img class="project-by-photo" src="$(esc(get(person, "photo", "/assets/img/team/placeholder.svg")))" alt="">
      <span>
        <strong>$(esc(pick(person, "name")))</strong><br>
        <span class="muted">$(esc(pick(person, "role")))</span>
      </span>
    </p>"""
    return """
<header class="page-hd project-hd">
  <div class="container">
    <p class="project-crumb">
      <a href="$(prefix())/projects/">$(esc(ui("projects", "back")))</a>
    </p>
    <span class="card-badge">$(esc(pick(area, "title")))</span>
    <h1>$(esc(pick(p, "title")))</h1>
    <p>$(esc(pick(p, "lead")))</p>
$(byline)
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
    p === nothing && return empty_state("people")
    hon = get(p, "honors_" * lang(), get(p, "honors_en", String[]))
    links = String[]
    haskey(p, "email")   && !isempty(p["email"])   && push!(links, """<a href="mailto:$(esc(p["email"]))">$(icon("envelope")) $(esc(p["email"]))</a>""")
    haskey(p, "scholar") && !isempty(p["scholar"]) && push!(links, """<a href="$(esc(p["scholar"]))" rel="noopener">$(icon("mortarboard")) $(esc(ui("people", "scholar")))</a>""")
    haskey(p, "nycu")    && !isempty(p["nycu"])    && push!(links, """<a href="$(esc(p["nycu"]))" rel="noopener">$(icon("building")) $(esc(ui("people", "nycu_hub")))</a>""")
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

function people_section(tier, label)
    body = cards_of(tier)
    if isempty(body)
        tier in ("lead", "phd", "msc") || return ""
        body = """<p class="people-tier-empty">$(esc(ui("people", "empty_tier")))</p>"""
        return """
<section class="people-tier" data-empty-tier="$(esc(tier))">
  <div class="section-head mt-5">
    <h2>$(esc(ui("people", label)))</h2>
  </div>
$(body)
</section>"""
    end
    return """
<section class="people-tier">
  <div class="section-head mt-5">
    <h2>$(esc(ui("people", label)))</h2>
  </div>
$(body)
</section>"""
end

hfun_people_leads()    = people_section("lead", "lead_head")
hfun_people_postdocs() = people_section("postdoc", "postdoc_head")
hfun_people_phd()      = people_section("phd", "phd_head")
hfun_people_msc()      = people_section("msc", "msc_head")

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

public_alumni() = public_alumni_records()

function hfun_people_alumni_link()
    isempty(public_alumni()) && return ""
    return """<p class="mt-5"><a class="link-arrow" href="$(prefix())/people/alumni/">$(esc(ui("people", "alumni_link"))) <span class="link-arrow-mark">&rarr;</span></a></p>"""
end

function hfun_people_alumni()
    as = public_alumni()
    isempty(as) && return empty_state("alumni")
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
    push!(hidden, """<input type="hidden" name="$(subj_name)" value="$(esc(ui("form", "subject")))">""")
    w3 && push!(hidden, """<input type="hidden" name="from_name" value="$(esc(ui("form", "sender")))">""")

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
                            ("scholar", "mortarboard", ui("people", "scholar")),
                            ("website", "globe", ui("people", "website")),
                            ("nycu", "building", ui("people", "nycu_hub")))
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
`{{person_portrait}}` — the identity block shared by every profile layout.

The DOM order is deliberately photograph, role, topic, links. CSS may place this
block in a rail on wide screens, but phones always encounter it immediately
after the person's name and before the narrative.
"""
function hfun_person_portrait()
    p = this_person()
    links = person_links(p)
    topic = String(get(p, "topic_" * lang(), get(p, "topic_en", "")))
    return """
<figure class="pi-portrait-frame">
  <img class="pi-portrait" src="$(esc(get(p, "photo", "/assets/img/team/placeholder.svg")))" alt="$(esc(pick(p, "name")))">
</figure>
<div class="profile-role-block">
  <p class="profile-role">$(esc(pick(p, "role")))</p>
$(isempty(topic) ? "" : """  <p class="profile-topic">$(esc(topic))</p>""")
</div>
$(isempty(links) ? "" : """<div class="pi-chips">""" * join(links, "") * "</div>")
"""
end

"""Compact, data-driven identity rows used by every public profile header."""
function person_header_identity(p)
    links = person_links(p)
    topic = String(get(p, "topic_" * lang(), get(p, "topic_en", "")))
    topic_parts = if isempty(topic)
        String[]
    elseif lang() == "zh"
        [strip(String(part)) for part in split(topic, r"[、與]") if !isempty(strip(String(part)))]
    else
        [strip(String(part)) for part in split(topic, r",\s*|\s+and\s+") if !isempty(strip(String(part)))]
    end
    expertise = if isempty(topic_parts)
        ""
    else
        items = join([
            """<span class="profile-expertise-item" role="listitem">$(esc(part))</span>"""
            for part in topic_parts
        ], "")
        """<span class="profile-header-divider" aria-hidden="true">|</span><span class="profile-expertise" role="list" aria-label="$(esc(ui("people", "expertise")))">$(items)</span>"""
    end
    return """
<div class="profile-header-details">
  <p class="profile-header-summary"><span class="profile-role">$(esc(pick(p, "role")))</span>$(expertise)</p>
$(isempty(links) ? "" : """  <div class="pi-chips">""" * join(links, "") * "</div>")
</div>
<figure class="pi-portrait-frame">
  <img class="pi-portrait" src="$(esc(get(p, "photo", "/assets/img/team/placeholder.svg")))" alt="$(esc(pick(p, "name")))">
</figure>
"""
end

"""
`{{person_header}}` — the page header band: breadcrumb, name and rule.

The role belongs to the identity block below the name. Repeating a tier eyebrow
here put role-like text before the name on phones and broke the shared reading
order.
"""
function hfun_person_header()
    p = this_person()
    return """
<header class="page-hd person-hd">
  <div class="container">
    <div class="person-hd-copy">
      <p class="project-crumb">
        <a class="link-arrow" href="$(prefix())/people/"><span class="link-arrow-mark">&larr;</span> $(esc(ui("people", "back")))</a>
      </p>
      <h1 class="pi-heading">$(esc(pick(p, "name")))</h1>
      <div class="pi-rule"></div>
    </div>
    <aside class="profile-header-identity" aria-label="$(esc(pick(p, "name")))">
$(person_header_identity(p))
    </aside>
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
    mine = filter(projects()) do project
        person = project_person(project)
        person !== nothing && String(person["id"]) == String(id)
    end
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
        <span class="pub-meta">$(esc(p["venue"])), $(p["year"])$(haskey(p, "citations") ? " &middot; " * string(p["citations"]) * " " * esc(ui("page", "citations")) : "")</span>
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
    its = copy(public_rows(data("news")["item"]))
    sort!(its; by = i -> i["date"], rev = true)
    return its
end

format_news_date(d) = lang() == "zh" ?
    "$(year(d)) 年 $(month(d)) 月 $(day(d)) 日" : Dates.format(d, "d u yyyy")

function news_tag_label(item)
    tag = String(get(item, "tag", ""))
    isempty(tag) && return ""
    section = data("ui")["news"]
    return haskey(section, tag * "_en") || haskey(section, tag * "_zh") ? ui("news", tag) : tag
end

"""`{{news}}` for all of them, `{{news 3}}` for the newest three."""
function hfun_news(params::Vector{String} = String[])
    its = news_items()
    isempty(its) && return empty_state("news")
    if !isempty(params)
        n = parse(Int, params[1])
        its = its[1:min(n, length(its))]
    end
    cards = join(["""
      <div class="col-md-4">
        <article class="news-card">
          <p class="news-date">$(format_news_date(i["date"]))<span class="news-tag">$(esc(news_tag_label(i)))</span></p>
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
          <p class="ns-date">$(format_news_date(i["date"]))<span class="news-tag">$(esc(news_tag_label(i)))</span></p>
          <h3 class="ns-title">$(esc(pick(i, "title")))</h3>
          <p class="ns-body">$(esc(pick(i, "body")))</p>
        </article>""" for (k, i) in enumerate(its)], "\n")

    navitems = join(["""
        <button class="ns-nav-item$(k == 1 ? " is-active" : "")" type="button" data-goto="$(k-1)"
                aria-label="$(esc(pick(i, "title")))">
          <span class="ns-nav-line"><span class="ns-nav-fill"></span></span>
          <span class="ns-nav-title">$(esc(pick(i, "title")))</span>
        </button>""" for (k, i) in enumerate(its)], "\n")

    return """
<section class="news-slider" id="newsSlider" aria-roledescription="carousel"
         aria-label="$(esc(ui("news", "carousel")))">
  <div class="container">
    <p class="ns-head">$(esc(ui("home", "news_head")))</p>

    <div class="ns-stage">
      <button class="ns-arrow ns-prev" type="button" aria-label="$(esc(ui("news", "previous")))">$(icon("chevron-left"))</button>
$(slides)
      <button class="ns-arrow ns-next" type="button" aria-label="$(esc(ui("news", "next")))">$(icon("chevron-right"))</button>
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
    navlinks = join(["""<a href="$(pre)$(href)">$(esc(ui("nav", k)))</a>""" for (k, href) in visible_nav()], "
          ")
    alumni = isempty(public_alumni()) ? "" :
        """<a href="$(pre)/people/alumni/">$(esc(ui("people", "alumni_link")))</a>"""
    return """
<footer class="lab-foot">
  <div class="container">
    <div class="row g-4">

      <div class="col-lg-6">
        <p class="foot-brand">$(esc(ui("site", "name")))</p>
        <p class="foot-uni">$(esc(ui("site", "uni")))</p>
        <p class="foot-addr">$(esc(ui("foot", "address")))</p>
      </div>

      <div class="col-12 col-lg-6">
        <p class="foot-head">$(esc(ui("foot", "nav")))</p>
        <nav class="foot-nav foot-nav-2col">
          $(navlinks)
          $(alumni)
$(join(["""          <a href="$(pre)$(href)">$(esc(ui("nav", k)))</a>""" for (k, href) in NAV_FOOT], "\n"))
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
