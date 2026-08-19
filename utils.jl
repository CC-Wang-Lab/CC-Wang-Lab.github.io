using TOML
using Dates

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

"""`{{ui nav research}}` -> the `research_en` / `research_zh` string in ui.toml."""
function hfun_ui(params::Vector{String})
    length(params) == 2 || error("{{ui section key}} needs exactly two arguments, got $params")
    section, key = params
    ui = data("ui")
    haskey(ui, section) || error("ui.toml has no [$section] section")
    return string(pick(ui[section], key))
end

ui(section, key) = string(pick(data("ui")[section], key))

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
#  Navigation and language switch
# ---------------------------------------------------------------------------

const NAV = [
    ("research",     "/research/"),
    ("capabilities", "/capabilities/"),
    ("industry",     "/industry/"),
    ("publications", "/publications/"),
    ("team",         "/team/"),
    ("news",         "/news/"),
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
        <img src="/assets/img/logo-mark.svg" alt="" width="38" height="38" class="brand-mark">
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
    return """
<section class="hero">
  <video class="hero-video" autoplay muted loop playsinline
         poster="/assets/video/hero-poster.jpg" aria-hidden="true" tabindex="-1">
    <source src="/assets/video/hero-boiling.mp4" type="video/mp4">
  </video>
  <div class="hero-veil"></div>
  <div class="hero-inner container">
    <h1 class="hero-title">$(esc(ui("hero", "title")))</h1>
    <p class="hero-lead">$(esc(ui("hero", "lead")))</p>
    <div class="hero-actions">
      <a class="btn btn-cta btn-lg" href="$(pre)/contact/">$(esc(ui("hero", "cta2")))</a>
      <a class="btn btn-ghost btn-lg" href="$(pre)/research/">$(esc(ui("hero", "cta1")))</a>
    </div>
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

function hfun_research_cards()
    pre = prefix()
    areas = data("research")["area"]
    cards = join(["""
      <div class="col-md-6 col-lg-4">
        <a class="card-area" href="$(pre)/research/#$(esc(a["id"]))">
          <span class="card-icon">$(icon(a["icon"]))</span>
          <h3 class="card-title">$(esc(pick(a, "title")))</h3>
          <p class="card-scope">$(esc(pick(a, "scope")))</p>
        </a>
      </div>""" for a in areas], "\n")
    return """<div class="row g-4">\n$(cards)\n</div>"""
end

"""Full research page: the same six areas, expanded, with anchors."""
function hfun_research_full()
    areas = data("research")["area"]
    blocks = join(["""
  <section class="area-block" id="$(esc(a["id"]))">
    <div class="area-head">
      <span class="card-icon">$(icon(a["icon"]))</span>
      <h2>$(esc(pick(a, "title")))</h2>
    </div>
    <p class="area-scope">$(esc(pick(a, "scope")))</p>
  </section>""" for a in areas], "\n")
    return blocks
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

function hfun_team_pi()
    p = pi_person()
    hon = get(p, "honours_" * lang(), get(p, "honours_en", String[]))
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
    <h2 class="pi-name">$(esc(pick(p, "name")))</h2>
    <p class="pi-role">$(esc(pick(p, "role")))</p>
    <ul class="pi-honours">
$(join(["      <li>$(esc(h))</li>" for h in hon], "\n"))
    </ul>
    $(paras(pick(p, "bio")))
    <p class="pi-links">$(join(links, " &middot; "))</p>
  </div>
</div>
"""
end

function hfun_team_leads()
    ls = filter(p -> get(p, "tier", "") == "lead" && get(p, "status", "") == "current", people())
    isempty(ls) && return ""
    cards = join(["""
      <div class="col-sm-6 col-lg-4">
        <div class="person-card">
          <img class="person-photo" src="$(esc(get(p, "photo", "/assets/img/team/placeholder.svg")))" alt="$(esc(pick(p, "name")))">
          <h3 class="person-name">$(esc(pick(p, "name")))</h3>
          <p class="person-role">$(esc(pick(p, "role")))</p>
          <p class="person-topic">$(esc(pick(p, "topic")))</p>
        </div>
      </div>""" for p in ls], "\n")
    return """<div class="row g-4">\n$(cards)\n</div>"""
end

function hfun_team_members()
    ms = filter(p -> get(p, "tier", "") == "member" && get(p, "status", "") == "current", people())
    isempty(ms) && return ""
    rows = join(["""
    <li class="person-row">
      <span class="person-row-name">$(esc(pick(p, "name")))</span>
      <span class="person-row-role">$(esc(pick(p, "role")))</span>
      <span class="person-row-topic">$(esc(pick(p, "topic")))</span>
    </li>""" for p in ms], "\n")
    return """<ul class="person-rows">\n$(rows)\n</ul>"""
end

function hfun_team_alumni()
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
        <nav class="foot-nav">
          $(navlinks)
          <a href="$(pre)/team/alumni/">$(esc(ui("team", "alumni_link")))</a>
        </nav>
      </div>

      <div class="col-6 col-lg-4">
        <p class="foot-head">$(esc(ui("foot", "contact")))</p>
        <nav class="foot-nav">
          <a href="mailto:$(esc(ui("foot", "email")))">$(icon("envelope")) $(esc(ui("foot", "email")))</a>
          <span class="foot-plain">$(icon("telephone")) $(esc(ui("foot", "phone")))</span>
          <a href="$(pre)/contact/">$(icon("geo-alt")) $(esc(ui("foot", "contact")))</a>
        </nav>
        <p class="mt-3"><a class="btn btn-ghost btn-sm" href="$(pre)/contact/">$(esc(ui("team", "join")))</a></p>
      </div>

    </div>

    <hr class="foot-rule">

    <p class="foot-fine">
      $(esc(ui("foot", "built")))
      &nbsp;&middot;&nbsp;
      $(esc(ui("foot", "dev"))) &mdash;
      <a href="mailto:meysam.gholampoor@gmail.com">meysam.gholampoor@gmail.com</a>
    </p>
  </div>
</footer>
"""
end
