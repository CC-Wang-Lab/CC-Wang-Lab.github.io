+++
title = "People"
descr = "Prof. Chi-Chuan Wang, the research leads, postdoctoral researchers and students of the lab."
lang = "en"
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

    <div class="section-head mt-5">
      <h2>{{ui people lead_head}}</h2>
    </div>
    {{people_leads}}

    <div class="section-head mt-5">
      <h2>{{ui people postdoc_head}}</h2>
    </div>
    {{people_postdocs}}

    <div class="section-head mt-5">
      <h2>{{ui people phd_head}}</h2>
    </div>
    {{people_phd}}

    <div class="section-head mt-5">
      <h2>{{ui people msc_head}}</h2>
    </div>
    {{people_msc}}

    <p class="mt-5"><a class="link-arrow" href="{{url people/alumni}}">{{ui people alumni_link}} <span class="link-arrow-mark">&rarr;</span></a></p>

  </div>
</div>
~~~
