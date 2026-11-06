# Learn style guide

Rules for every article in `content/learn/`. The daily job follows this file, and so should
any person who writes for Learn. The public version is `/learn/editorial-policy/`.

## The job of an article

Answer one question people actually type or ask an AI, better than anyone else on the
internet: accurate, cited, plain-English, and useful today. The penguin makes people
smile. The facts make people trust us. Never trade the second for the first.

## Evidence rules (non-negotiable)

1. **Every health claim and every number is cited** with `[n]` right after the claim.
2. **Source quality, best first:** systematic reviews and meta-analyses (Cochrane, PubMed);
   large cohort studies; randomized trials; public health guidance (CDC, NIH/NHLBI/NIA,
   WHO, NHS, AHA, ACSM, the U.S. Physical Activity Guidelines). Avoid blogs, brands,
   news articles (cite the study they cover instead), and single small studies when a
   review exists.
3. **Open every source and read it.** Cite it only for what it actually says, and keep
   the number exactly as reported. If you can't open a source (paywall, bot wall), find
   the PubMed abstract or another copy, or don't cite it. **Never invent a study, author,
   year, URL, or number.**
4. **Match language to the evidence.** Observational studies show links ("is linked to",
   "people who walk more tend to"), not cause and effect. Trials can support "lowers" or
   "improves". Say when evidence is limited or mixed.
5. Prefer recent evidence (last ~10 years) unless an older study is the landmark one.
6. 5–10 sources for clusters, 8–15 for pillar guides.

## Safety rules

- No diagnosis, dosing, or treatment instructions. Never suggest stopping or changing
  a medication; say "talk to your doctor".
- Anything about heart disease, high blood pressure, diabetes, pregnancy, injuries,
  older adults with falls risk, or eating disorders gets a clear "talk to your doctor
  first" section.
- Every page already ends with a health note (the template adds it). Don't repeat it.

## Weight and bodies

- Neutral, non-stigmatizing language. Say "weight", "body weight", "people with higher
  weight". Never "fat", "obese people", "beach body", "earn your dinner", "burn off that
  pizza", before/after framing, or calories as punishment.
- Lead with health outcomes (blood sugar, heart, mood, sleep), not appearance.
- Be honest: walking alone usually produces modest weight loss. Don't oversell.

## Voice

- **Body:** a smart, warm friend who reads studies. Grade-8 reading level. Short
  paragraphs (1–3 sentences). Active voice. "You", not "one". No hype words
  ("miracle", "secret", "hack", "game-changer"), no fear-mongering.
- **The penguin (Gary) appears in front matter only:**
  - `gary`: one punchy line, edgy Gen Z/millennial humor. He roasts procrastination,
    excuses, couches, and himself. **Never** bodies, weight, health conditions, age,
    disability, or identity.
  - `signoff`: a short closer in his voice.
  - Good: "Your arteries called. They want 30 minutes and zero excuses."
    "Bold of you to read about walking while sitting down."
  - Bad: anything about someone's size, shape, or "letting themselves go".
- No penguin jokes in the article body.

## Structure

```
---
title: <the exact question, ending in ?> (pillar guides: a guide title)
pillar: heart | longevity | weight | mind | basics
description: <≤155 chars, contains the answer>
answer: <2–3 plain sentences that fully answer the question, with the key number. No markdown, no citations.>
published: YYYY-MM-DD
updated: YYYY-MM-DD   (only when revised later)
keywords: <8–12 comma-separated phrases people search>
pose: waddler-hyped | waddler-celebrating | waddler-neutral | couch-resting | couch-shocked | couch-slumped
gary: <one line>
signoff: <one line>
reviewed_by:   (leave out until a credentialed reviewer has actually reviewed it)
status: published
---
```

- Body: an intro (2–3 short paragraphs, don't repeat the answer verbatim), then 4–7
  `##` sections phrased as questions where natural, `###` for sub-points.
- Include one practical "how to start / try this" list.
- `## FAQ`: 3–5 `###` questions (under 60 characters), each answered in 1–3 sentences.
  They must be different from the `##` headings.
- `## Sources`: numbered `1.`, `2.`… in order of first use:
  `Author AB, et al. Title. *Journal*. Year. https://...` (PubMed URLs preferred for studies).
- Markdown allowed: `##`, `###`, paragraphs, `- ` lists, `1. ` lists, `**bold**`,
  `*italic*`, `[text](https://...)` or `[text](/learn/<slug>/)`, `> ` quotes. No HTML,
  tables, or images.
- Length: clusters 900–1,800 words of body; pillar guides 2,000–3,500.

## Internal links

- Link to the pillar guide: `[walking and your heart](/learn/walking-heart-health/)`.
- Link to 2+ other published Learn articles where relevant (check `content/learn/`).
  Only link to articles that exist; `scripts/check.py` fails on broken links.
- When a new article is a better answer for something an older article mentions, add a
  link from the older article too and set its `updated` date.

## Pillar guides

A pillar's file is named after its hub slug (`walking-heart-health.md` for `heart`).
It's the definitive overview of that topic: what walking does, how much, for whom,
how to start, and links out to every cluster in the pillar. Its `title` is a guide
title, not a question (e.g. "Walking and your heart: the complete guide").

## Updating articles

When research changes, edit the article, add or update sources, and set `updated`.
Never change `published`.
