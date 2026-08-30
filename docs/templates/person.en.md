+++
title = "Member Name"
person = "your-id"
lang = "en"
+++

~~~
{{person_header}}
~~~

@@page-body,profile-page
@@container
@@profile-layout
@@profile-narrative,prose

## PLACEHOLDER

**Copy this file** to `people/<your-id>.md`, change `person = "..."` in the front matter to the public id
from `_data/team.toml`, and write. Then do the same for `zh/people/<your-id>.md`.

Everything in the header above comes from your row in `team.toml`, so do not repeat your name, role
or email here.

## What I work on

One or two paragraphs. Say what you measure or build, and what question it answers. Write it for an
engineer who has never met this laboratory.

## Method

What rig, what instruments, what solver, what conditions.

## Images

Put them in `_assets/img/team/<your-id>/` and use them like this:

```markdown
![](/assets/img/team/your-id/rig.jpg)
```
@@
@@profile-record
~~~
{{person_facts}}
~~~
@@
@@
@@
@@
