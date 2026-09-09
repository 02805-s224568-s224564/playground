---
name: go-nuts
description: Weekly plumbing for the 02805 "go nuts" post on the Marvel/Wikipedia network. Fetch the week's brief, scaffold the notebook and the post, copyedit a draft, self-review with the course rubric, run the publish checklist, verify hygiene and the live deploy. Never does the analysis or writes the findings.
argument-hint: "start <week> [url] | post <week> \"<title>\" | copyedit [file] | review [file] | publish | check"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# go-nuts

Plumbing for the weekly post. The group and the notebook produce every number,
figure and finding. You fetch, scaffold, check and copyedit.

Repo state right now:
!`ls _posts notebooks notebooks/briefs 2>/dev/null || true`

## Setup

- Run every script from the repo root with the venv Python, `.venv/bin/python`
  (Windows: `.venv\Scripts\python.exe`). If `.venv` is missing, run `./scripts/dev-setup.sh` first.
- Scripts live in `${CLAUDE_SKILL_DIR}/scripts/`; each prints `--help`.
- Arguments this run: `$ARGUMENTS`. The first word is the mode. With no arguments, or an unknown mode, print the table below and stop.

## Modes

| Mode | Does | Read first |
|---|---|---|
| `start <week> [url]` | fetch the brief, scaffold the notebook | references/data.md |
| `post <week> "<title>"` | scaffold the `_posts/` file | references/post-guide.md |
| `copyedit [file]` | tighten a draft without changing a claim | references/post-guide.md |
| `review [file]` | critique with the course rubric, no edits | references/review-rubric.md, references/rules.md |
| `publish` | run the checklist, verify the deploy | references/publish-checklist.md |
| `check` | hygiene, then the live deploy | nothing |

### start
1. `.venv/bin/python ${CLAUDE_SKILL_DIR}/scripts/fetch_brief.py <week-or-url>`. Exit 2 means the week is not live yet: say so and stop.
2. Read `notebooks/briefs/week<N>.md`. Use `suggested_slug` unless the user gave a slug.
3. `.venv/bin/python ${CLAUDE_SKILL_DIR}/scripts/new_notebook.py <N> <slug>`.
4. Reply with the brief's "This week's ideas and tools" list verbatim, the notebook path, and `jupyter lab notebooks/week<N>-<slug>.ipynb`. Do not propose analyses beyond the brief's own list.

### post
1. Require `notebooks/week<N>-*.ipynb`. If missing, say so and stop; suggest `start`.
2. Ask for a title if none was given. A question makes the best title.
3. `.venv/bin/python ${CLAUDE_SKILL_DIR}/scripts/new_post.py <N> "<title>"`.
4. List the `<!-- go-nuts: -->` markers the user has to fill. Do not fill them; the findings are theirs.

### copyedit
1. Default file: the newest `_posts/*.md`. Read it and references/post-guide.md.
2. Edit for grammar, clarity, length and the four-part shape. Never change a number, a claim or an interpretation. Never add content that is not in the draft or the notebook. If a claim is unclear, ask.
3. List every edit, one line each.

### review
1. Default file: the newest `_posts/*.md`. Read it, references/review-rubric.md, references/rules.md and `notebooks/briefs/week<N>.md`.
2. Answer in the rubric's format: what works, one concrete thing to try, checklist. No edits.

### publish
1. Run references/publish-checklist.md top to bottom. Stop at the first failure and report it.
2. Commit and push only after the user confirms each step. Never `git add -f data/`.
3. End with the Teams message and the reminder to comment on another group's post.

### check
1. `.venv/bin/python ${CLAUDE_SKILL_DIR}/scripts/check_hygiene.py`. Report every FAIL with its fix.
2. If the tree is clean and pushed, `.venv/bin/python ${CLAUDE_SKILL_DIR}/scripts/check_deploy.py`.

## Hard rules

- Never invent a finding, a number or an interpretation. Everything comes from the notebook or the user.
- Never pad. Four sections, one figure or table, 300 to 600 words.
- Figures only through `figure.html` or `interactive.html` includes, never markdown images: the site lives under `/playground`.
- No `layout:` in post front matter; `_config.yml` sets it.
- Never overwrite an existing notebook or post. The scripts refuse; do not work around them.
- Names: `notebooks/week<N>-<slug>.ipynb`, `assets/figures/week<N>-<slug>.png|html`, `_posts/YYYY-MM-DD-<slug>.md`.
- Every figure has real alt text.
- When unsure about a convention, read the reference file. Do not guess.
