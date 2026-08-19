<!--
Global page variables for the CC Wang Lab website.
NOTE: no `prepath` — this is a USER site (CC-Wang-Lab.github.io), served at the root.
      Adding a prepath here would break every CSS and asset path.
-->
+++
author = "CC Wang Lab"
mintoclevel = 2
lang = "en"

ignore = ["node_modules/", "tmp.md", "docs/", ".claude/", "CLAUDE.md", "THIRD-PARTY-LICENSES.md", "_tmp/"]

generate_rss = false
website_title = "CC Wang Lab"
website_descr = "Thermal engineering research at National Yang Ming Chiao Tung University"
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
#
#   ""                                   -> the form falls back to mailto:.
#                                           Works today, needs no account, but it
#                                           opens the visitor's mail app instead
#                                           of sending anything itself.
#   "https://formspree.io/f/XXXXXXXX"    -> Formspree, free tier
#   "https://api.web3forms.com/submit"   -> Web3Forms (also set form_access_key)
#
# Create the free account, point it at ccwang@nycu.edu.tw, paste the endpoint
# here. Nothing else changes.
form_endpoint   = ""
form_access_key = ""
form_to         = "ccwang@nycu.edu.tw"
+++

\newcommand{\R}{\mathbb R}
