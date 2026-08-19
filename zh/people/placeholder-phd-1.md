+++
title = "範例 - 成員姓名"
person = "placeholder-phd-1"
lang = "zh"
+++

~~~
{{person_header}}
~~~

@@page-body
@@container
@@project-body,prose

## 範例頁面

**請複製本檔案**至 `zh/people/<你的 id>.md`，將前置設定中的 `person = "..."` 改為你在
`_data/team.toml` 的 id，然後開始撰寫。英文版請同樣複製到 `people/<你的 id>.md`。

上方標頭的所有資訊皆來自 `team.toml` 中你的資料列，因此請勿在此重複姓名、職稱或電子郵件。

## 研究內容

一至兩段文字。說明你量測或建置什麼，以及回答什麼問題。設想讀者是從未接觸本實驗室的工程師。

## 方法

使用的實驗台、儀器、求解器與操作條件。

## 圖片

請置於 `_assets/img/team/<你的 id>/`，並如下引用：

```markdown
![](/assets/img/team/your-id/rig.jpg)
```
@@
~~~
{{person_projects}}
~~~
@@
@@
