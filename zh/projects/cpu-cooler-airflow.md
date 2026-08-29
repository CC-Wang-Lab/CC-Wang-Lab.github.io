+++
title = "CPU 塔型散熱器之氣流分析"
project = "cpu-cooler-airflow"
lang = "zh"
+++

~~~
{{project_header}}
~~~

@@page-body
@@container
@@project-body,prose

## 研究問題

熱阻可概括散熱器的整體性能，卻無法呈現決定該性能的實際氣流路徑。部分空氣可能繞過鰭片組、在風扇輪轂後方回流，或自塔頂離開而未接觸鰭片。將這些旁通路徑視覺化，可辨識最值得修改的幾何區域。

## 方法

本研究針對裝有塔型散熱器的 ATX 主機板，在多個風扇轉速下進行穩態 CFD 分析。所得速度場匯入即時算繪系統，並於入口、側面及出口釋放無質量粒子以追蹤流動路徑。粒子持續運動時即可切換風扇轉速，使不同操作條件得以直接比較。

~~~
<figure class="project-figure">
  <video controls muted playsinline preload="metadata"
         poster="/assets/img/projects/cpu-cooler-airflow.jpg">
    <source src="/assets/video/cfd-cpu-cooler.mp4" type="video/mp4">
  </video>
  <figcaption>通過鰭片組的流線粒子，以速度大小著色。</figcaption>
</figure>
~~~

## 觀察到什麼

鰭片組下游的深色氣流代表已吸收熱量的空氣；其折返主機板的路徑，顯示下一版導流罩應限制回流的區域。

## 相關紀錄與論文

目前未列出相關論文或實驗紀錄。
@@
@@
@@
