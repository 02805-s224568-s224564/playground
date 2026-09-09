# Publish checklist

Run from the repo root, top to bottom. Stop at the first failure and report
it. `PY` is `.venv/bin/python` (Windows: `.venv\Scripts\python.exe`); the
scripts are in `.claude/skills/go-nuts/scripts/`.

1. **Hygiene, strict.** `PY .claude/skills/go-nuts/scripts/check_hygiene.py --strict`
   Every line must be PASS. Leftover `<!-- go-nuts:` markers and template example figures count as failures here.

2. **The notebook runs clean and regenerates its figures.**
   `PY .claude/skills/go-nuts/scripts/run_notebook.py notebooks/week<N>-*.ipynb`
   This proves every figure in the post can be rebuilt from the notebook in the repo.

3. **Package tests.** `PY -m pytest -q -m "not network"`

4. **Local build.** Skip with a note if Ruby is not installed.
   `bundle exec jekyll build`, then confirm `_site/assets/figures/week<N>-*` exists and `_site/<YYYY>/<MM>/<DD>/<slug>/index.html` contains `<img` or `<iframe`.
   For a visual check: `bundle exec jekyll serve` and open <http://localhost:4000/playground/> (the `/playground/` part matters).

5. **`git status`.** Only `_posts/`, `notebooks/`, `notebooks/briefs/` and `assets/figures/` should be changed. Nothing under `data/`. No file that is not part of this week's post.

6. **Commit and push, each after the user confirms.**
   `git add <the files from step 5>` and commit with the message `post(week<N>): <title>`, then `git push`.

7. **Deploy.** `PY .claude/skills/go-nuts/scripts/check_deploy.py _posts/<file>`
   Waits for the GitHub Actions run of HEAD, then fetches the live post and checks every image, iframe and stylesheet answers 200.

8. **Hand over.** Print the Teams message for the user to paste:

   > Week <N> from Six Degrees of Marvel: <live post URL>

   and the reminder: read the other groups' posts and leave what works plus one
   concrete thing to try on at least one of them before the next session.
