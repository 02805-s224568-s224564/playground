# The course rules, fixed all semester

Source: week 1, exercise 1.8 "Go nuts with your LLM",
<https://sunelehmann.com/socialgraphs2026-web/weeks/week1.html#go-nuts>.
Course content by Sune Lehmann, CC BY-SA 4.0. Quoted verbatim so nobody has to
re-read the page every week.

## Read the rules once

> Every week of this course ends this way, so read the rules once.
>
> 1. Your group should start a **public website** — a GitHub Pages site your LLM helps you build and style, your personal corner of the internet.
> 2. Each week you add one post to the website: use the week's tools to get something fun out of the **shared playground dataset**. Be as free and creative as possible. Go nuts with your friends and an LLM. Try something. Make figures, build. Write about what you found (or didn't).
>
> By December you will have done the "interactive data story" eight times before it counts for anything — and the whole class will have accumulated insight on one dataset.
>
> The playground: the 303 characters in Wikipedia's Category:Marvel Comics superheroes and the links between their pages — a dense, hub-riddled little universe (Spider-Man alone is linked by a third of it), sitting right there in public. This half of the course we mine its structure; from week 5, its text.

## The shape of a post

> Write it up as your first post: what you asked, what you did, one figure or table, what surprised you.

## Then, always

> **Then, always:** post your site link in this week's Teams channel by Monday evening · read what other groups made · leave **constructive, friendly criticism** on at least one other group's post (what works, one concrete thing to try). Honing your critical eye on each other's work is half the point. We announce a winner from last week at the start of the next session.

## The same, as a table

| Duty | When | How |
|---|---|---|
| Post is live | Monday evening | push to `main`; GitHub Actions deploys |
| Link posted | Monday evening | this week's Teams channel |
| Comment on at least one other group's post | before the next session | what works, plus one concrete thing to try |
| Winner announced | start of the next session | (week 2 says 09:00 Wednesday) |

## Standing options

- Stretch, from week 1: re-derive a corner of the dataset with the Wikipedia API and check the snapshot. Wikipedia may answer 403 without a User-Agent header; `marvel/wiki.py` sets one.
- Weeks 2–4: crawl a different Wikipedia category of your own choosing and run the week's toolkit there instead.

## The one iron rule (course front page, "Groups")

> There is a single iron rule: everyone must be able to solve everything. The tests are individual, on paper, and they do not care who in your group understood it.
