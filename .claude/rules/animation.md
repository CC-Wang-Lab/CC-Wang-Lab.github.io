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

## Motion starts running, for everyone

**This rule replaced an earlier one, on purpose. Read the history before changing it back.**

There were two earlier versions, and both were wrong in the same direction:

1. The first did `display: none` on the hero video under `prefers-reduced-motion`. A visitor got a
   still image with no way to play it, and no clue why.
2. The second kept the video visible but refused to start it, and refused to advance the news
   slider. Better, but the site still looked frozen to the same people.

**Why those visitors are not an edge case:** on Windows, "reduce motion" is just
Settings > Accessibility > Visual effects > Animation effects = Off. Many people switch that off
for performance, not for motion sensitivity. The site owner is one of them, which is how the fault
was found — three times.

### What the site does now

`_assets/js/motion.js` owns one flag. The hero video, the news slider, the partners marquee and
the typed line all read it.

| | Behaviour |
|---|---|
| Default | **Running.** `prefers-reduced-motion` is deliberately not consulted. |
| The control | One visible, keyboard-reachable button in the hero pauses and resumes **everything** at once |
| Memory | The choice is stored in `localStorage` and survives reloads and page changes |
| Pausing | Never leaves a half-typed word or a half-faded slide; each element settles on a complete state |

**The requirement this satisfies is WCAG 2.2.2 "Pause, Stop, Hide"** — motion that starts on its own
and runs past five seconds must have a mechanism to stop it. That is normative. Honouring
`prefers-reduced-motion` is good practice, not normative, and here it was doing more harm than good.

### Testing this: always clear the flag afterwards

The pause choice is stored in `localStorage` under `labMotion` and it **persists across pages and
visits**, which is correct behaviour and also a trap while testing.

Setting `window.LabMotion.set(false)` from a console or an automation script leaves the reviewer's
own browser paused. It happened once: the partners marquee was reported as "not animated" when the
animation was running perfectly and the flag was simply off, set by a screenshot script minutes
earlier.

```js
localStorage.removeItem("labMotion");   // run this at the end of any motion test
```

Before reporting motion as broken, read the flag first:

```js
localStorage.getItem("labMotion")            // "off" explains everything
getComputedStyle(document.querySelector(".pt-track")).animationPlayState
```

### If you ever change this back

You must keep a control that starts the motion, and it must be visible without hovering. A page
that is frozen with no visible way to start it is the fault this rule exists to prevent.

## The old rule, kept for reference

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
