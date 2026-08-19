# Animation, and the reduced-motion rule

Every value below was **measured from the imec.com stylesheets** on 2026-08-19, not invented. If a
number here changes, change it because imec changed, or because somebody decided differently on
purpose, and say which.

| Effect | Rule |
|---|---|
| Card lift | `translateY(-1.25em)`, `transition: transform .25s ease-out`. Image and text lift together. |
| Card shadow | `0 .9375rem 1.5625rem 0 rgba(24,24,40,.15)`, deepening on hover |
| Image zoom | `scale(1.025) translateZ(0)` — 2.5%, and it should read as depth, not as a zoom |
| Link underline | `::after` bar, `scaleX(0)` to `scaleX(1)`, `transform-origin: left center` |
| Arrow nudge | `translateX(.625rem)` |
| Slider slides | stacked, `opacity 0` to `1`, `transition: opacity .5s ease-out`. **Cross-fade, never a sideways slide.** |
| Slider progress line | `13.75rem x .25rem` track, fill bar `translateX(-100%)` to `translateX(0)` over the dwell time |
| Slider arrows | `top: 50%; transform: translateY(-50%)`, outside the slide at `+/- 2.1875rem`, nudging `+/- .3125rem` |

## The reduced-motion rule

**Never hide anything for `prefers-reduced-motion: reduce`.**

*Why: the first version of the hero did `display: none` on the video under that query. The result
was a still image with no way to play it, and the person reviewing the site saw exactly that,
because on Windows "reduce motion" is only Settings > Accessibility > Visual effects > Animation
effects = Off. Plenty of people switch that off for performance. They are not an edge case.*

What to do instead:

| Kind of motion | Under reduced motion |
|---|---|
| **Hover effects** | **Keep them.** They are user-initiated and last a quarter of a second. |
| **Autoplaying video** | Do not start it. Leave it visible on its poster and show a play button. |
| **Auto-advancing slider** | Do not advance. Leave the arrows and the title navigation working. |
| **Smooth scrolling, fade-in** | Switch off. Nothing is lost. |

The check that matters: **turn Windows animation effects off, reload, and confirm nothing has
disappeared and nothing is unreachable.**
