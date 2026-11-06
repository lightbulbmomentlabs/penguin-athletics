# Daily Learn article: instructions for the scheduled job

You are drafting one article for the Learn section of penguinathletics.com, the website
for Penguin, a funny iPhone walking app. A human reviews and merges your pull request;
merging publishes it. You never merge, never push to `main`, and never publish anything
yourself.

## Steps

1. Start from the latest `main`. Create a branch `learn/<slug>`.
2. Read `content/STYLE.md` fully. It is the rulebook.
3. Open `content/backlog.md` and take the **first unchecked** topic (`- [ ]`). Each line is
   `- [ ] <slug> | <pillar> | <question or guide title>`. If the slug already exists in
   `content/learn/`, check it off and take the next one.
4. Research it on the web. Find 5–10 authoritative sources (8–15 for a pillar guide),
   following the evidence rules in STYLE.md. **Open every source and confirm it says what
   you will cite it for.** If a site blocks you, use the PubMed abstract or drop it.
   Never cite anything you didn't read. Never invent anything.
5. Read 2–3 existing published articles in `content/learn/` to match tone and format,
   and to find good internal links.
6. Write `content/learn/<slug>.md`. Set `published` to today's date (America/Chicago).
   Set `status: published` (the human merge is the gate).
7. Check the topic off in `content/backlog.md` (`- [x]`).
8. If the new article answers something an existing article mentions, add an internal
   link from that article and set its `updated` date to today.
9. Run, and fix everything until all three pass:
   - `python3 scripts/build_learn.py`
   - `python3 -m unittest scripts/test_learnlib.py`
   - `python3 scripts/check.py`
10. Commit the source, the backlog change, and the regenerated `public/` files with the
    message `Learn: <title>`. Push the branch and open a pull request titled
    `Learn: <title>`.

## Pull request description (so review takes five minutes)

```
**<title>** · <pillar> · <word count> words · <n> sources

**The short answer:** <answer field>

**Claims to check**
| Claim | Source | What the source says (exact quote or number) |
|---|---|---|
| ... | [1] | ... |

**Judgment calls:** anything uncertain, uncited advice, sources you couldn't open, and
anything a reviewer should look at first.

**Gary's line:** "<gary>"
```

## If something goes wrong

- If you can't find enough trustworthy sources for the topic, don't force it. Move the
  topic to the bottom of the backlog with a note `(needs better sources)` and draft the
  next one instead.
- If the checks fail and you can't fix them, still open the PR, mark it as a draft, and
  explain what's failing.
- One article per run. Don't open a second PR if one from today is already open.
