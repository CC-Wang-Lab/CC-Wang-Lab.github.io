# Partner logos - where each file came from

**This file is generated.** `scripts/prepare-partner-logos.py` writes it from
`_data/partners.toml` and `../_internal-docs/partner-logo-map.toml`, so a logo
cannot arrive without its row. Do not edit it by hand; edit the map and re-run.

## How these were obtained

Two sources, and they are not equal.

**The lab's own set, 60 files, supplied 2026-09-01.** This is what
`NEEDED.md` had been asking for since 2026-08-19: the collage the lab already
uses to show who it works with. It is both more reliable and more defensible
than hunting each company's website, because somebody at the lab chose it.

**Wikimedia Commons, 12 files, downloaded 2026-08-19.** Kept only where the
artwork is the SAME mark as the lab's own file. A real vector beats a raster at
every size, so where the two agree the vector wins. Where they disagree, the
lab's file wins and the reason is written beside the row.

Every file was looked at, one by one, before being accepted. That check is not
optional:

- A search for "ASE Group logo" returned **the European Space Agency banner**.
- A search for "Lite-On logo" returned an unrelated mark reading "TL".
- A search for "Google logo" returned the **Google Play** logo from 2012-2015.

All three were rejected. A logo that is nearly right is worse than a name in
plain text, because a visitor who knows the company sees the mistake at once.

## What was done to each file

Nothing that changes the mark, except where a row says so.

1. **Trimmed.** Several arrived with the mark occupying under 5% of the canvas.
2. **Sized.** Each logo gets its own display size from its aspect ratio and ink
   coverage, so a 10:1 wordmark is not a sliver beside a square badge. The law
   is in `scripts/prepare-partner-logos.py`.
3. **Rendered at 3x** that size and optimised.
4. **Repaired, two of them only.** A mark drawn in white for a dark background
   cannot survive this site's light theme. Those rows carry a `fix` note.

**No logo was traced to SVG.** Measured on 12 of these files: a traced SVG came
out 14x heavier than the same logo as an optimised PNG, 2,440 KB against 179 KB,
and was not faithful either. One file reached 1.4 MB on its own.

## Copyright

The Wikimedia files are **public domain**: simple wordmarks below the threshold
of originality, so no copyright subsists and there is no licence to comply with.

The lab's own files are the marks of the organisations named. **Public domain
for copyright is not permission for trademark**, and that question is handled by
how the logos are used, not by where the files came from:

- The heading reads **"Organizations we have worked with"**, which states a
  fact. It is not "Our clients" and not "Trusted by", either of which would
  imply endorsement.
- A notice under the strip says the marks belong to their owners and that no
  endorsement is implied.
- Logos render greyscale until hover, which uses less of each mark.

**The NDA question is still open and is not a question this file can answer.**
A non-disclosure agreement often forbids revealing that a relationship exists at
all. Prof. Wang's office must mark every organisation whose agreement forbids
disclosure, and those rows must be DELETED from `_data/partners.toml`.

## The files


| File | Organisation | Source | Note |
|---|---|---|---|
| `accton.svg` | Accton Technology | Wikimedia Commons, 2026-08-19 |  |
| `advantech.svg` | Advantech | Wikimedia Commons, 2026-08-19 |  |
| `ansys.svg` | Ansys | Wikimedia Commons, 2026-08-19 |  |
| `ase-holdings.png` | ASE Holdings | the lab's own set, `日月光投控.png` |  |
| `avc.png` | AVC | the lab's own set, `avc.png` | **Name not yet confirmed by the lab.** |
| `celsia.png` | Celsia | the lab's own set, `celsia.png` |  |
| `changyang.png` | ChangYang | the lab's own set, `彰洋.png` |  |
| `chaun-choung-technology.png` | Chaun-Choung Technology | the lab's own set, `尼得科超眾_CCI.png` |  |
| `chroma-ate.png` | Chroma ATE | the lab's own set, `Chroma.png` |  |
| `chung-yo-materials.png` | Chung Yo Materials | the lab's own set, `中祐精材.png` |  |
| `chunghwa-telecom-laboratories.png` | Chunghwa Telecom Laboratories | the lab's own set, `中華電信研究院.png` | `chunghwa.svg` names the PARENT, 中華電信 / Chunghwa Telecom. This row is the Laboratories, 中華電信研究院, which is what the lab's own file shows. |
| `cooler-master.svg` | Cooler Master | Wikimedia Commons, 2026-08-19 |  |
| `coretronic.png` | Coretronic | the lab's own set, `Coretronic.png` |  |
| `cpc.svg` | CPC Corporation, Taiwan | Wikimedia Commons, 2026-08-19 |  |
| `cryomax-cooling-system.png` | Cryomax Cooling System | the lab's own set, `cryomax.png` | **Name not yet confirmed by the lab.** |
| `delta.svg` | Delta Electronics | Wikimedia Commons, 2026-08-19 |  |
| `expert-international.png` | Expert International | the lab's own set, `expert.png` |  |
| `far-tech-engineering.png` | FAR Tech Engineering | the lab's own set, `遠技fartech.png` |  |
| `formosa-chemicals-fibre.png` | Formosa Chemicals & Fibre | the lab's own set, `台灣化學纖維公司.png` |  |
| `formosa-heavy-industries.png` | Formosa Heavy Industries | the lab's own set, `台朔重工公司.png` |  |
| `formosa-petrochemical.png` | Formosa Petrochemical | the lab's own set, `台塑石化公司.png` |  |
| `formosa-plastics.png` | Formosa Plastics | the lab's own set, `台灣塑膠公司.png` |  |
| `gigastorage-corporation.png` | Gigastorage Corporation | the lab's own set, `國碩科技.png` |  |
| `google.png` | Google | the lab's own set, `google.png` |  |
| `heatscape.png` | Heatscape | the lab's own set, `heatscape.png` |  |
| `hermes-epitek.png` | Hermes-Epitek | the lab's own set, `漢民科技_Hermes tech.png` |  |
| `hitachi.png` | Hitachi | the lab's own set, `Hitachi.png` | `hitachi.svg` is the 'Inspire the Next' lockup with a red rule. At 3rem tall the tagline is mush and the rule reads as a stray line. |
| `hon-precision.png` | Hon.Precision | the lab's own set, `hontech.png` | **Name not yet confirmed by the lab.** |
| `hot-cool.png` | Hot Cool | the lab's own set, `高揚國際實業.png` | **Name not yet confirmed by the lab.** |
| `industrial-technology-research-institute.png` | Industrial Technology Research Institute | the lab's own set, `中研院.png` |  |
| `innodisk.png` | innodisk | the lab's own set, `Innodisk.png` |  |
| `intel.svg` | Intel | Wikimedia Commons, 2026-08-19 |  |
| `inventec.svg` | Inventec | Wikimedia Commons, 2026-08-19 |  |
| `jentech-precision.png` | Jentech Precision | the lab's own set, `jentech.png` | **Name not yet confirmed by the lab.** |
| `jws-technology.png` | JWS Technology | the lab's own set, `智惠創富.png` |  |
| `kaori-heat-treatment.png` | Kaori Heat Treatment | the lab's own set, `kaori.png` |  |
| `lanner-electronics.png` | Lanner Electronics | the lab's own set, `Lanner.png` |  |
| `lemtech.png` | LemTech | the lab's own set, `lemtech.png` |  |
| `liangchi-group.png` | Liangchi Group | the lab's own set, `良機集團.png` | Its own opaque white plate removed; the mark was invisible in both themes. |
| `lite-on.png` | Lite-On | the lab's own set, `Liteon.png` |  |
| `long-time-technology.png` | Long Time Technology | the lab's own set, `榮炭科技.png` |  |
| `long-victory-instruments.png` | Long Victory Instruments | the lab's own set, `長聖儀器.png` |  |
| `meta-green-cooling-technology.png` | Meta Green Cooling Technology | the lab's own set, `元鈦科技.png` |  |
| `metal-industries-research-development-centre.png` | Metal Industries Research & Development Centre | the lab's own set, `金屬工業研界發展中心.png` | **Name not yet confirmed by the lab.** |
| `metropole-industrial.png` | Metropole Industrial | the lab's own set, `metropole.png` |  |
| `national-chung-shan-institute-of-science-and-technology.png` | National Chung-Shan Institute of Science and Technology | the lab's own set, `國家中山科學研究院.png` | White lettering repainted in the seal's navy `#36368b`; it was invisible on the light page. **Name not yet confirmed by the lab.** |
| `national-science-and-technology-council.png` | National Science and Technology Council | the lab's own set, `國科會.png` |  |
| `novatek.png` | Novatek | the lab's own set, `聯詠novatek.png` |  |
| `patech-fine-chemicals.png` | Patech Fine Chemicals | the lab's own set, `patech.png` |  |
| `pegatron.svg` | Pegatron | Wikimedia Commons, 2026-08-19 |  |
| `precision-machinery-research-development-center.png` | Precision Machinery Research & Development Center | the lab's own set, `PMC.png` |  |
| `promise-technology.png` | Promise Technology | the lab's own set, `Promise Technology.png` |  |
| `rayvatek.png` | Rayvatek | the lab's own set, `rayvatek.png` | **Name not yet confirmed by the lab.** |
| `rechi-precision.png` | Rechi Precision | the lab's own set, `瑞智精密.png` |  |
| `ritex-machinery.png` | Ritex Machinery | the lab's own set, `ritex.png` | **Name not yet confirmed by the lab.** |
| `sakura.png` | Sakura | the lab's own set, `sakura.png` | **Name not yet confirmed by the lab.** |
| `satti.png` | SATTI | the lab's own set, `超尊科技.png` | **Name not yet confirmed by the lab.** |
| `sunon.png` | Sunon | the lab's own set, `Sunon_Green.png` |  |
| `sunwood-foundry-works.png` | Sunwood Foundry Works | the lab's own set, `申伍鑄造.png` |  |
| `swico.png` | SWICO | the lab's own set, `swico.png` |  |
| `t-global-technology.png` | T-Global Technology | the lab's own set, `T-Global.png` |  |
| `taiwan-asahi-diamond-industrial.png` | Taiwan Asahi Diamond Industrial | the lab's own set, `台灣鑽石工業股份有限公司.png` |  |
| `taiwan-heat-transfer.png` | Taiwan Heat Transfer | the lab's own set, `台灣熱傳股份有限公司.png` |  |
| `taiwan-hodaka-technology.png` | Taiwan Hodaka Technology | the lab's own set, `Hodaka.png` |  |
| `taiwan-space-agency.png` | Taiwan Space Agency | the lab's own set, `TASA.png` |  |
| `teco.svg` | TECO | Wikimedia Commons, 2026-08-19 |  |
| `toshiba.svg` | Toshiba | Wikimedia Commons, 2026-08-19 |  |
| `tsmc.png` | TSMC | the lab's own set, `tsmc.png` | `tsmc.svg` is the wordmark alone. The lab's file is the full mark, wafer chequerboard included. |
| `vigour-group.png` | Vigour Group | the lab's own set, `vigour group.png` | **Name not yet confirmed by the lab.** |
| `visera-technologies.png` | VisEra Technologies | the lab's own set, `VisEra.png` |  |
| `wavepro.png` | WavePro | the lab's own set, `WavePro.png` |  |
| `wistron.svg` | Wistron | Wikimedia Commons, 2026-08-19 |  |
