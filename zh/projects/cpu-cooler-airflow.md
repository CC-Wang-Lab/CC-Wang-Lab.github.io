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
@@page-narrow,prose

## 研究問題

塔型散熱器通常只用一個數字評價：熱阻。但這個數字掩蓋了空氣實際的流向。有一部分空氣根本沒有進入鰭片組：它從外殼旁溢出、在風扇輪轂後方回流，或是從塔頂離開而未接觸任何鰭片。

**看見這些溢流，才知道該修改幾何的哪一部分。**

## 方法

對裝有塔型散熱器的 ATX 主機板進行穩態 CFD 分析，並求解多個風扇轉速工況。接著將速度場讀入即時繪圖引擎，於入口、側面與出口釋放無質量粒子，追蹤其在流場中的路徑。

結果不是一張靜態等值圖。粒子持續運動的同時即可切換風扇轉速，因此不同工況之間的差異可直接看見，而不需要比對兩張圖。

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

鰭片組後方顏色較深的氣流，是已經吸熱的空氣。這股氣流折返朝向主機板的位置，就是下一版外殼應該封閉的地方。

## 相關紀錄與論文

*有連結時請於此處補上。*
@@
@@
@@
