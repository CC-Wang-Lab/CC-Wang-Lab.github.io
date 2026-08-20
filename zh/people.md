+++
title = "研究成員"
descr = "王啟川教授、研究主持群、博士後研究員與研究生。"
lang = "zh"
+++

~~~
<header class="page-hd">
  <div class="container">
    <h1>{{ui nav people}}</h1>
    <p>{{ui people page_lead}}</p>
  </div>
</header>

<div class="page-body">
  <div class="container">

    {{people_pi}}

<!--
  ONLY PROF. WANG IS SHOWN HERE, ON PURPOSE (2026-08-20).

  Everyone else in team.toml is still a lorem-ipsum placeholder, and a page of
  invented colleagues does the laboratory more harm than a short page does.

  TO BRING THE REST BACK, add these six blocks in place of this comment. They
  are written without the braces on purpose: Franklin does NOT resolve a
  template call inside an HTML comment, it leaves it as literal text, and the
  deploy workflow fails the build when it finds one in __site. Put the double
  braces back as you paste each line in.

    section-head mt-5  ->  h2: ui people lead_head       then  people_leads
    section-head mt-5  ->  h2: ui people postdoc_head    then  people_postdocs
    section-head mt-5  ->  h2: ui people phd_head        then  people_phd
    section-head mt-5  ->  h2: ui people msc_head        then  people_msc
    section-head mt-5  ->  h2: ui people table_head
                           p:  ui people table_lead      then  people_table

  Every one of those generators still exists in utils.jl and still works.

  Widen [people] page_lead in _data/ui.toml at the same time. It was
  narrowed to name only Prof. Wang, because the old line promised research
  leads and researchers that this page no longer shows.
-->

    <p class="mt-5"><a class="link-arrow" href="{{url people/alumni}}">{{ui people alumni_link}} <span class="link-arrow-mark">&rarr;</span></a></p>

  </div>
</div>
~~~
