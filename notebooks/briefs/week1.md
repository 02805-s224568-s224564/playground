---
week: 1
topic: "Networks"
suggested_slug: networks
source: https://sunelehmann.com/socialgraphs2026-web/weeks/week1.html
fetched: 2026-09-09
---

# Week 1 — Networks

Source: <https://sunelehmann.com/socialgraphs2026-web/weeks/week1.html>. Course content by Sune Lehmann, CC BY-SA 4.0.

## Sections on the page

- 0 · How to read/watch/work in the age of AI (#how-to-read-watch-work-in-the-age-of-ai)
- 1 · Why networks? (#why-networks)
- 2 · Nodes, edges, and all that (#nodes-edges-and-all-that)
- 3 · Choosing the representation (#choosing-the-representation)
- 4 · Your toolbox (#your-toolbox)
- 5 · Degree distributions (#degree-distributions)
- 6 · Seeing a network (#seeing-a-network)
- 7 · Group Exercise (#group-exercise)
- Essentials (#essentials)
- Goodies (#goodies)

## This week's ideas and tools

This week — the bootstrap edition:

1. Power up your group's site on GitHub Pages. Let your agent do as much as possible; make it yours — name it, style it, put your group on it.
2. Grab the week-1 release of the shared network — the edge list and the node roster on the [course data page](https://sunelehmann.com/socialgraphs2026-web/data/) (frozen snapshot, so every group computes on identical data; the page tells you how to load it without losing the isolated nodes — yes, there are isolated nodes, and they are worth a look).
3. Explore, freely, with this week's ideas and tools: degree distributions (linear and log–log!), in- versus out-degree — who is linked *to* most, who links out most, and why are those different people? Draw the network. Make art. Go nuts. Find the islands outside the giant component. Or chase something we didn't think of — surprise us.
4. Write it up as your first post: what you asked, what you did, one figure or table, what surprised you. (Stretch: re-derive a corner of the dataset yourself with the Wikipedia API — see below — and check the snapshot.)

## Group exercise, verbatim

### 1.8 — Go nuts with your LLM 🚀 Builder · every week, from now on

Every week of this course ends this way, so read the rules once.

1. Your group should start a **public website** — a GitHub Pages site your LLM helps you build and style, your personal corner of the internet.
2. Each week you add one post to the website: use the week's tools to get something fun out of the **shared playground dataset**. Be as free and creative as possible. Go nuts with your friends and an LLM. Try something. Make figures, build. Write about what you found (or didn't).

By December you will have done the "interactive data story" eight times before it counts for anything — and the whole class will have accumulated insight on one dataset.

The playground: the 303 characters in Wikipedia's [Category:Marvel Comics superheroes](https://en.wikipedia.org/wiki/Category:Marvel_Comics_superheroes) and the links between their pages — a dense, hub-riddled little universe (Spider-Man alone is linked by a third of it), sitting right there in public. This half of the course we mine its structure; from week 5, its text.

This week — the bootstrap edition:

1. Power up your group's site on GitHub Pages. Let your agent do as much as possible; make it yours — name it, style it, put your group on it.
2. Grab the week-1 release of the shared network — the edge list and the node roster on the [course data page](https://sunelehmann.com/socialgraphs2026-web/data/) (frozen snapshot, so every group computes on identical data; the page tells you how to load it without losing the isolated nodes — yes, there are isolated nodes, and they are worth a look).
3. Explore, freely, with this week's ideas and tools: degree distributions (linear and log–log!), in- versus out-degree — who is linked *to* most, who links out most, and why are those different people? Draw the network. Make art. Go nuts. Find the islands outside the giant component. Or chase something we didn't think of — surprise us.
4. Write it up as your first post: what you asked, what you did, one figure or table, what surprised you. (Stretch: re-derive a corner of the dataset yourself with the Wikipedia API — see below — and check the snapshot.)

**The Wikipedia API, for when you want to go beyond the snapshot.** The course hands you the Marvel network ready-made. But the data comes from somewhere, your go-nuts posts are allowed to reach past the frozen snapshot, and your final project will need a cool dataset that could well be a crawl of a domain of its own. Wikipedia serves every page in two forms: the rendered HTML you read in a browser, and the raw wiki-source behind it — internal links sit in the wiki-source as `[[Page name]]`, which is exactly how the Marvel network's edges were harvested — and the API hands you either one programmatically. My old-school video walkthrough is [here](https://www.youtube.com/watch?v=9l5zOfh0CRo) (it is Python-2 era; the ideas hold, your agent speaks the current dialect). One practical note: Wikipedia may answer `403` unless your request carries a User-Agent header identifying your client.

**Then, always:** post your site link in this week's Teams channel by Monday evening · read what other groups made · leave **constructive, friendly criticism** on at least one other group's post (what works, one concrete thing to try). Honing your critical eye on each other's work is half the point. We announce a winner from last week at the start of the next session.
