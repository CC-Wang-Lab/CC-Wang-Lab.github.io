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
@@page-narrow,prose

## The question

A tower cooler is judged by one number, its thermal resistance. That number hides where the air
actually goes. Some of it never reaches the fin stack at all: it spills around the shroud, or
recirculates behind the fan hub, or leaves through the top of the tower without touching a fin.

**Seeing the spill is what tells you which part of the geometry to change.**

## The method

Steady-state CFD of an ATX board with a tower cooler, solved at several fan speeds. The velocity
field is then read back into a real-time renderer, where massless particles are released at the
inlet, at the sides and at the outlet, and traced through the flow.

The result is not a still contour plot. Fan speed can be changed while the particles keep moving,
so the difference between operating points is visible directly instead of being compared across two
figures.

~~~
<figure class="project-figure">
  <video controls muted playsinline preload="metadata"
         poster="/assets/img/projects/cpu-cooler-airflow.jpg">
    <source src="/assets/video/cfd-cpu-cooler.mp4" type="video/mp4">
  </video>
  <figcaption>Streamline particles through the fin stack, coloured by velocity magnitude.</figcaption>
</figure>
~~~

## What it shows

The dark plume behind the fin stack is air that has already picked up heat. Where that plume bends
back toward the board is where the next revision of the shroud should close.

## Notes and publications

*Add links here as they appear.*
@@
@@
@@
