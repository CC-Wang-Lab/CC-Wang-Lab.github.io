+++
title = "Publications"
descr = "Selected publications organized by research theme, with links to Professor Chi-Chuan Wang's complete publication records."
lang = "en"
+++

~~~
<header class="page-hd">
  <div class="container">
    <h1>{{ui nav publications}}</h1>
    <p>{{ui page pubs_lead}} {{fill lab_outputs}} {{ui page pubs_outputs}} {{fill lab_articles}} {{ui page pubs_articles}}</p>
    <!-- Icon plus short label, side by side. The citation count used to sit in
         the first button; a number that ages badly does not belong in one. -->
    <p class="pub-links">
      <a class="btn btn-ghost btn-sm" href="https://scholar.google.com/citations?user=QlIdSPIAAAAJ&amp;hl=en" rel="noopener">
        <i class="bi bi-mortarboard"></i> Google Scholar
      </a>
      <a class="btn btn-ghost btn-sm" href="https://scholar.nycu.edu.tw/en/persons/chi-chuan-wang/" rel="noopener">
        <i class="bi bi-building"></i> {{ui page pubs_hub}}
      </a>
    </p>
  </div>
</header>

<div class="page-body">
  <div class="container">
    {{publications}}
  </div>
</div>
~~~
