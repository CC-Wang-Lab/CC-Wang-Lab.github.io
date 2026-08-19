The central problem with the current concept is that it is **too close to an academic lab website with industrial decoration**. For this lab, the stronger positioning is the reverse: **an unusually research-strong thermal-engineering R&D group that companies can actually work with**.

The publications, citation metrics and professor credentials establish authority. They should not dominate the information architecture.

## 1. Five more websites worth copying

I checked these sites today, August 19, 2026; all five are live.

| Site | URL | ONE feature to steal | Why it fits this lab |
|---|---|---|---|
| **Center for Energy-Smart Electronic Systems (ES2), Binghamton University** | `https://www.binghamton.edu/es2/` | **Research areas written around industrial problems, not academic disciplines.** | This is the closest analogue I found: its research page explicitly talks about acting as a research arm for industry and then presents air cooling, liquid cooling, two-phase/immersion cooling, control, data-centre optimization, etc. almost exactly in the territory Wang Lab occupies. citeturn302774view0 |
| **Center for Environmental Energy Engineering (CEEE), University of Maryland** | `https://ceee.umd.edu/` | **Make industry collaboration a concrete operating model.** | CEEE does not merely say "we collaborate with industry": it organizes research into industry-facing consortia and exposes a clear sponsor pathway; that is much more convincing for a large HVAC&R/thermal group than a wall of logos. citeturn302774view1 |
| **Stanford SystemX Alliance** | `https://systemx.stanford.edu/` | **An "Industry Affiliates" page that explains the value of collaboration before displaying companies.** | For a Taiwan lab working with electronics and technology companies under NDA, this is the right model: explain what a company gains, how engagement works, and what technical network it can access; logos are secondary evidence. citeturn302774view2 |
| **MIT.nano** | `https://mitnano.mit.edu/` | **Present facilities as capabilities.** | MIT.nano tells the reader what can actually be fabricated, characterized or investigated rather than giving them a gallery of expensive equipment; Wang Lab should do exactly this with thermal test rigs, liquid cooling, boiling, airflow, heat exchangers, instrumentation and computation. citeturn302774view3 |
| **imec** | `https://www.imec-int.com/en` | **Separate "Expertise" from "What we offer."** | This is particularly useful for a Taiwan lab serving semiconductor, electronics and data-centre companies: one dimension answers "what do you know?" while another answers "what can you do with us?", without requiring disclosure of confidential customers. citeturn302774view4 |

### The one I would study most closely

**ES2.**

Not because its website is especially beautiful. It isn't.

Study it because its underlying information model is almost exactly what you need. Its research page says, in effect:

**industrial problem → research capability → technical approach**

rather than:

**professor → papers → students → news.**

It even describes industrial members helping define research directions and lists air cooling, warm-water liquid cooling, two-phase and immersion cooling, embedded cooling, controls and data-centre optimization. citeturn302774view0

For your purpose, that is more valuable than copying another polished hero section.

---

# 2. Critique of the eight-item site map

Your current navigation is:

> Home | Research | Facilities | Publications | People | Partners | News | Contact

I would **not launch that navigation**.

Three items are wrong in concept: **Home, Facilities, Partners**.

And one important item is missing: **Industry**.

## Home is dead weight

The lab name/logo should return to Home.

You already have eight navigation items plus:

- language switch
- theme switch

So the header will have ten interactive elements before you even consider a collaboration CTA.

Drop **Home**.

---

## "Partners" should not exist at launch

This is the biggest structural error.

You know that:

- most collaborations are confidential;
- logos require explicit permission;
- testimonials probably cannot be obtained;
- the page will consequently be almost empty.

So you are knowingly creating a top-level navigation destination whose initial job is to demonstrate **what you cannot disclose**.

That is backwards.

Worse, an empty "Our Clients" section does not communicate confidentiality. It communicates:

> perhaps they don't have clients.

Do **not** launch an empty logo wall.

Replace **Partners** with:

# Industry

That page can be excellent on day one without naming a single company.

It should answer:

- What kinds of industrial problems does the lab work on?
- What capabilities can companies access?
- What sectors does it work across?
- What forms can a collaboration take?
- What evidence is there that the group can deliver?
- Who should an engineer contact?

Your legitimate evidence is already unusually strong:

**20+ active industrial projects**, roughly **50–60 researchers**, **12 patents**, and a PI who spent **21 years at ITRI** before returning to academia.

Those facts do far more work than six logos.

Later, when permissions arrive, add:

**Selected collaborators**

inside Industry.

Not "Our Clients".

"Clients" makes the university laboratory sound like a consultancy. Some projects may indeed function like client work, but **Industry Collaborations** or **Selected Industry Partners** is safer and more accurate.

---

## "Facilities" is the wrong word

For an academic visitor, "Facilities" means:

> Show me your equipment.

For an industrial engineer, the question is:

> Can you test my cold plate?

> Can you measure boiling behaviour?

> Can you validate airflow?

> Can you model the system before we build it?

> Can you run experiments at the scale I care about?

Therefore rename it:

# Capabilities

Facilities become evidence underneath capabilities.

For example:

**Two-phase thermal management**

- pool-boiling experimental rigs
- instrumentation
- high-speed/video diagnostics
- modelling
- relevant publications

**Data-centre airflow**

- rack/server experiments
- airflow measurements
- CFD
- PINN/data-driven modelling
- control

That is much stronger than:

> Laboratory A  
> Fluke instrument  
> Flow meter  
> Thermal camera  
> Test bench

MIT.nano's distinction is useful here: its public-facing page is explicitly called **Research Capabilities**, even though the physical infrastructure is enormous. citeturn302774view3

---

## "People" is potentially your maintenance disaster

A 60-person photo-card grid sounds reasonable in a wireframe and becomes horrible after two years.

The problem isn't generating it from TOML.

**Automation does not solve stale data.**

If someone leaves the lab and nobody edits the TOML file, Franklin will reproduce the wrong information perfectly forever.

And with:

> Faculty / Research Fellow / Postdoc / PhD / MSc / Alumni

you eventually get hundreds of cards.

I would rename the page **Team** and divide it differently.

### Main Team page

**Leadership & research leads**

Larger cards, photographs, area of responsibility.

Then:

**Current researchers**

Compact cards or rows:

> Name  
> Research Fellow  
> Liquid cooling / two-phase thermal management

You don't need sixty mini-CVs.

Then one link:

> View alumni →

### Alumni page

Separate archive entirely.

Organize by departure year or cohort rather than academic rank.

And add maintenance metadata to your TOML:

```toml
status = "current"
joined = 2024
last_verified = "2026-08-01"
```

Ideally your build should warn when a supposedly current member has not been verified for, say, 12 months.

That is the difference between **data-driven** and actually **maintainable**.

---

# My revised navigation

I would use:

> **Research | Capabilities | Industry | Publications | Team | News | About | [Discuss a project]**

with:

- lab logo/name → Home
- 中文 / English switch
- dark/light icon

The square brackets above mean the final item should visually be a CTA button, not another equal-weight navigation link.

### What goes where

| Top-level | Purpose |
|---|---|
| **Research** | What scientific/engineering problems the lab investigates |
| **Capabilities** | What the lab can actually model, build, measure, test and validate |
| **Industry** | How companies can work with the lab + NDA-safe evidence of industrial activity |
| **Publications** | Selected research grouped by theme + Scholar link |
| **Team** | Leadership + current researchers + separate alumni archive |
| **News** | Current activity, results, awards, talks, projects where disclosure is permitted |
| **About** | Prof. Wang, lab history, ITRI background, awards, numbers, NYCU context |
| **Discuss a project** | Contact specifically for industrial/research collaboration |

I prefer **Discuss a project** over **Contact**.

"Contact" is administrative.

"Discuss a project" tells the industrial visitor why they would click.

For recruitment, use a secondary **Join the lab** link within Team/About and in the footer. It does not deserve equal prominence with industrial collaboration on every page.

---

# 3. The first thirty seconds

Your Taiwanese thermal-engineering manager is not primarily evaluating whether Professor Wang is famous.

They're running a much more practical decision tree.

## Their actual priority order

### 1. "Do these people solve my kind of problem?"

This is overwhelmingly first.

The data-centre supplier is scanning for:

> liquid cooling  
> cold plates  
> immersion  
> two-phase  
> airflow  
> rack thermal management  
> controls  
> modelling  
> testing

The packaging engineer may be scanning for:

> high heat flux  
> package-level thermal management  
> boiling  
> phase change  
> heat pipes  
> thermal resistance  
> simulation  
> experiments

If those signals are not visible almost immediately, the visitor leaves.

**Your video does not solve this.**

A beautiful pool-boiling video is visually relevant, but unless I already know what I'm watching, it is just bubbles.

---

### 2. "Can they actually execute this?"

Now they want evidence of capability.

Not citations.

They want:

> What experimental systems do you have?

> What can you measure?

> Can you model it?

> Can you validate it experimentally?

> Can you work at component level and system level?

> Do you have enough researchers to execute a serious company project?

This is where **50–60 researchers** and **20+ active industrial projects** become extremely persuasive.

Your proposed homepage does not currently give enough capability evidence.

The research cards tell me what you **study**.

They do not necessarily tell me what you **can do for a project**.

That distinction should exist everywhere on the site.

---

### 3. "Have companies trusted them with real engineering work?"

Now industrial credibility matters.

Your current answer is supposed to be:

> Our Clients

followed by...

nothing.

That is potentially the worst element on the proposed homepage.

At launch, remove the entire logo wall.

Replace it with something like:

## Industrial R&D at scale

> **20+ active industry projects**  
> Experimental, computational and AI-assisted thermal engineering across electronics cooling, data centres, HVAC&R and thermal systems.

Then link:

> How we collaborate →

You don't need to apologize for confidentiality.

On the Industry page, one sentence is enough:

> Many industrial collaborations are confidential; organizations are identified publicly only where disclosure has been approved.

Then move on to the capabilities.

Stanford SystemX and Maryland CEEE both demonstrate the useful principle: **industry engagement can itself be described as a product/value proposition rather than reduced to company logos.** citeturn302774view2turn302774view1

---

### 4. "Who is behind this?"

Now Professor Wang matters enormously.

And this is an area where your proposed homepage undersells what you have.

You have an extraordinarily strong credibility story:

> Chair Professor, NYCU  
> 29,400 citations  
> h-index 85  
> ASHRAE Fellow  
> ASME Fellow  
> 21 years at ITRI

The important point is **not to dump all of that into a giant biography**.

Give him perhaps one compact credibility block:

> **Prof. Chi-Chuan Wang**  
> Chair Professor, Mechanical Engineering, NYCU  
> ASHRAE Fellow · ASME Fellow · 29,400 citations  
> 21 years of industrial R&D at ITRI before returning to academia

That last fact may actually be more persuasive to the company engineer than the h-index.

It says:

> this professor understands industrial R&D.

Your existing homepage architecture doesn't surface that story clearly enough.

---

### 5. "What would working with them actually look like?"

This comes surprisingly quickly.

The visitor needs an obvious path:

> I have a thermal problem. What happens next?

Your current button says:

> **Work with us**

I would change it.

"Work with us" is ambiguous.

It can mean:

- apply for a PhD;
- apply for a postdoc;
- hire us;
- collaborate academically;
- sponsor research.

Use:

> **Discuss an R&D project**

or:

> **Industry collaboration**

For recruiting:

> Join the lab

should remain separate.

---

### 6. "Are these people active now?"

Finally, recent activity validates everything above.

Three recent news items are useful.

Especially if they show things like:

- a new experiment;
- an industrially relevant paper;
- a conference presentation;
- a new test facility;
- an award;
- a publicly disclosed collaboration.

This is where News earns its homepage position.

---

# Your proposed homepage, item by item

I would change the sequence substantially.

### Current

> Hero video  
> Numbers  
> Research cards  
> Clients  
> News  
> Join

### I would launch this instead

> **1. Hero: what the lab actually does**  
> **2. Industrial/capability proof**  
> **3. Research areas**  
> **4. Capabilities / experimental + modelling infrastructure**  
> **5. Prof. Wang / lab credibility**  
> **6. Selected research outputs**  
> **7. Latest news**  
> **8. Industry collaboration CTA**

And possibly a small Join-the-Lab secondary CTA near the bottom/footer.

---

## 1. Hero

Keep the video.

But don't let the video be the message.

The text must answer **what** and **where** immediately.

For example, conceptually:

> **Thermal engineering from chips to energy systems**  
> Experimental and computational research in electronics cooling, data-centre thermal management, HVAC&R and advanced heat-transfer systems at NYCU.

Then:

**Explore research**  
**Discuss an R&D project**

The video becomes evidence supporting the statement.

Not the statement itself.

And caption or otherwise identify the footage. A visitor should be able to understand that they are seeing **CFD airflow** and **pool-boiling experiments**, not generic visual decoration.

---

## 2. Replace your current numbers

You proposed:

> 29,400 citations · h-index 85 · 578 papers · 20+ industry projects

There is a factual problem here:

### **578 papers is wrong.**

According to your own verified figures, **578 is research outputs**, including:

- journal articles,
- conference contributions/articles,
- reviews,
- patents,
- etc.

Do not convert that into "578 papers".

It is exactly the kind of little credibility error that an academic or technical visitor can detect.

More importantly, I would not use four bibliometric numbers anyway.

For this website, a stronger band is approximately:

> **50–60 researchers**  
> **20+ active industry projects**  
> **12 patents**  
> **29,400 citations**

Now every number tells a different story:

**scale · industrial demand · technology output · academic authority**

"H-index 85" can live on the About page.

---

## 3. Research cards

Keep them, but six cards is probably the maximum.

And do not make them merely category names.

Weak:

> Electronic Cooling

Better:

> **Electronics & AI Cooling**  
> Air, liquid, two-phase and immersion thermal management from packages to racks.

The card should immediately expose scope.

The full research page can reveal the taxonomy underneath.

---

## 4. Kill "Our Clients" at launch

Completely.

No grey placeholder logos.

No "coming soon".

No empty whitespace waiting for approvals.

No generic handshake stock photograph.

Replace it with **Industry Collaboration**.

When you eventually have perhaps **six or more meaningful permissions**, introduce a restrained "Selected collaborators" row.

Until then, twenty NDA-protected projects are **not an embarrassment you need to conceal**. They are strong evidence of demand.

---

## 5. Add capabilities before News

This is the largest missing homepage component.

Give me maybe four capability groups:

| Capability | Example evidence |
|---|---|
| **Experimental thermal engineering** | boiling, heat exchangers, liquid cooling, thermal characterization |
| **Electronics & data-centre testing** | airflow, rack/system thermal behaviour, package/component cooling |
| **Modelling & simulation** | thermal-fluid models, CFD, system simulation |
| **AI-assisted engineering** | PINNs, forecasting, smart thermal control |

This answers the industrial manager's second question:

> **Can they actually do anything useful for me?**

---

# What would make that manager close the tab?

Several things.

**An empty client-logo wall.** It makes an active industrial lab appear commercially unproven.

**A vague hero headline.** If it says something like "Advancing Thermal Science for a Sustainable Future", I still do not know whether you can solve my cold-plate problem.

**Sixty researcher photographs before I understand the lab's capability.** Organization is not evidence.

**A facilities page full of equipment names without engineering context.** Engineers buy capabilities, not photographs of instruments.

**Bibliometrics presented as the primary proof of industrial competence.** Twenty-nine thousand citations are impressive; they do not tell me whether you can instrument and validate my prototype.

**Slow hero video.** If the most sophisticated element of the homepage makes the site feel sluggish, the technology demonstration has damaged the technology brand.

**An ambiguous "Work with us" button.** I shouldn't have to click it to discover whether it means "become a PhD student" or "bring us an industrial problem."

**Stale people/news information.** For a laboratory claiming 20+ current industrial projects and 50–60 people, a news page last updated eighteen months ago or profiles of people who left years earlier does disproportionate reputational damage.

And the most serious failure:

> **Making me work to discover what you can actually do.**

---

# The homepage test I would use

After looking at the homepage for 30 seconds, a first-time visitor should be able to answer five questions without opening another page:

| Question | Required answer |
|---|---|
| **Who are they?** | Prof. Chi-Chuan Wang's thermal-engineering laboratory at NYCU |
| **What do they work on?** | Electronics/data-centre cooling + broader thermal/HVAC systems |
| **Can they execute?** | ~60 people, experimental + modelling capability |
| **Does industry trust them?** | 20+ active industrial projects; PI has deep ITRI background |
| **What do I do if I have a problem?** | Click **Discuss an R&D project** |

Your current homepage answers roughly **two and a half of those five**.

It establishes academic stature and research breadth. It does **not yet establish execution capability or industrial engagement strongly enough**.

That is the main design correction I would make before writing any Franklin templates.

### In one sentence

**Do not design this as "Professor Wang's academic website, but larger"; design it as the public front door of a 60-person thermal-engineering R&D organization whose unusual advantage is that it combines serious academic authority with industrial-scale execution.**