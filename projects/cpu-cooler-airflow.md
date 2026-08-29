+++
title = "Airflow through a CPU tower cooler"
project = "cpu-cooler-airflow"
lang = "en"
+++

~~~
{{project_header}}
~~~

@@page-body
@@container
@@project-body,prose

## The question

Thermal resistance summarizes a cooler's overall performance but does not reveal the airflow paths that determine it. Air may bypass the fin stack, recirculate behind the fan hub, or leave through the top of the tower without contacting the fins. Visualizing these bypass paths identifies the parts of the geometry most likely to benefit from revision.

## The method

Steady-state CFD was performed for an ATX board fitted with a tower cooler at several fan speeds. The resulting velocity fields were imported into a real-time renderer, where massless particles were released at the inlet, sides and outlet and traced through the flow. Fan speed can be changed while the particles remain in motion, allowing operating points to be compared directly.

~~~
<figure class="project-figure">
  <video controls muted playsinline preload="metadata"
         poster="/assets/img/projects/cpu-cooler-airflow.jpg">
    <source src="/assets/video/cfd-cpu-cooler.mp4" type="video/mp4">
  </video>
  <figcaption>Streamline particles through the fin stack, colored by velocity magnitude.</figcaption>
</figure>
~~~

## What it shows

The dark plume downstream of the fin stack represents air that has absorbed heat. Its return path toward the board identifies the region where the next shroud revision should limit recirculation.

## Notes and publications

No related publications or laboratory notes are currently listed.
@@
@@
@@
