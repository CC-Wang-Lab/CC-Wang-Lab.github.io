<!--
Global page variables for the CC Wang Lab website.
NOTE: no `prepath` — this is a USER site (CC-Wang-Lab.github.io), served at the root.
      Adding a prepath here would break every CSS and asset path.
-->
+++
author = "CC Wang Lab"
mintoclevel = 2
lang = "en"

# `lead` is declared here only so the variable EXISTS. It is never the value
# a page shows: every detail page sets its own, and `card_words` in utils.jl
# stops the build when one does not.
#
# THIS DECLARATION IS NOT WHAT MAKES THE CARDS WORK, and the next person will
# try it, so: `pagevar` cannot be used to read these at all. Franklin's
# PAGEVAR_DEPTH guard (src/converter/markdown/md.jl:38, src/utils/vars.jl:253)
# is incremented and never decremented, and returns the default once one page
# has pulled in more than six unprocessed pages. A 26-card index gets six
# answers and twenty blanks, silently. `card_words` reads the .md file instead.
lead = ""

# Franklin COPIES every path not named here into __site, and __site is what gets
# published. Found on the first real deploy, 2026-08-19: the site was serving
# /_data/partners.toml, /scripts/shoot.py, /Project.toml and /Manifest.toml.
#
# `_data/` is the one that matters. It holds every organisation name, the whole
# team list and the unpublished notes beside them, and it was fetchable directly
# even though nothing links to it and it is in no sitemap.
#
# Ignoring `_data/` does NOT break the build. The generators in utils.jl read it
# from the SOURCE tree with TOML.parsefile; this list only decides what is copied
# to the output.
#
# Keep this a Julia comment. An HTML comment inside the +++ block is a parse
# error, because Franklin evaluates the whole block as Julia code.
ignore = ["node_modules/", "tmp.md", "docs/", ".claude/", ".superpowers/", "CLAUDE.md",
          "THIRD-PARTY-LICENSES.md", "_tmp/",
          "_data/", "scripts/",
          "Project.toml", "Manifest.toml", "package.json", "package-lock.json"]

generate_rss = false
website_title = "CC Wang Lab"
website_descr = "Experimental and computational thermal-engineering research at National Yang Ming Chiao Tung University."
website_url   = "https://cc-wang-lab.github.io/"

# --- lab facts, used by the numbers band and the credibility block ---
# Verified 2026-08-19 from Google Scholar and the NYCU Academic Hub.
lab_citations   = "29,400"
lab_hindex      = "85"
lab_outputs     = "578"
lab_articles    = "439"
lab_patents     = "12"
lab_projects    = "20+"
lab_people      = "50-60"

# --- the contact form ---
# GitHub Pages has no server, so the form on /contact/ posts to a third party.
# Until an endpoint is set it falls back to mailto:, which opens the visitor's
# own mail program instead of sending anything itself.
#
# TO MAKE IT SEND, FOR REAL, TO JULIA
#
#   1. Go to https://web3forms.com and enter juliahsieh@nycu.edu.tw.
#      No account and no password: the access key arrives by email.
#   2. Paste that key into form_access_key below.
#   3. Set form_endpoint to https://api.web3forms.com/submit
#
# THE DESTINATION IS BAKED INTO THE KEY, NOT INTO THIS FILE. Web3Forms delivers
# to whichever address created the key. `form_to` below is only used by the
# mailto: fallback and by the "it did not send" message. If the key is created
# with a different address, mail goes there and nothing here will say so.
#
# Formspree works too - set form_endpoint to https://formspree.io/f/XXXXXXXX and
# leave form_access_key empty. utils.jl emits the right hidden field names for
# whichever endpoint it sees; the two services do not share them.
form_endpoint   = ""
form_access_key = ""
form_to         = "juliahsieh@nycu.edu.tw"
+++

\newcommand{\R}{\mathbb R}

<!--
  THE DETAIL-PAGE MARKERS.

  A facility or project page writes its own words and its own layout, in
  Markdown, using these. The full reasoning is in the banner comment above
  `current_record` in utils.jl; the short version is that `@@name ... @@` is
  the only form Franklin nests correctly while still running the content
  through Markdown, and an environment is what gives it a NAME at both ends.
  Four bare `@@` five levels deep is what this replaces.

  THESE ARE A FLOOR, NOT A CEILING. A page may ignore all of them and write
  its own `@@` blocks. `oil-immersion-heat-transfer-enhancement` uses none of
  the split shapes, only `{{figrow}}`, because it has five pictures and no
  words at all.
-->

\newenvironment{page}{@@page-body,setup-study-page @@container @@setup-rows}{@@ @@ @@}

<!-- A NEWS ARTICLE. One column of prose, in the page's own words.
     Not `page`: that is the setup-study wrapper and it carries a figure-row
     track a news article has no use for. -->
\newenvironment{article}{@@page-body @@container @@prose,news-article}{@@ @@ @@}

\newenvironment{words}{@@setup-notes,prose}{@@}
\newenvironment{note}{@@setup-notes,prose,setup-notes--single}{@@}

\newenvironment{level}[1]{@@setup-split,setup-split--solved @@setup-split-words @@setup-notes,prose}{@@ @@ {{figrow #1}} @@}

\newenvironment{split}[1]{@@setup-split @@setup-split-words @@setup-notes,prose}{@@ @@ {{figrow #1}} @@}
