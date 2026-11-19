---
name: researchforge-panel
description: "Use when assessing ideas. Run panel and publish privately."
version: 0.3.7
author: ResearchForge team + OpenAI Codex
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [research, multi-agent, novelty, evidence, debate]
    category: research
---

# ResearchForge Panel Skill

Assess a research idea through three independent roles: an innovation-first
Theorist, a sceptical Challenger, and an evidence-first Arbiter. This skill is
the one Hermes entry point; it coordinates bounded subagents and returns a
traceable decision rather than treating a model score as proof of novelty.

## When to Use

Use when a researcher asks whether an idea is novel, valuable, feasible, or
worth pursuing, especially when cross-disciplinary prior work may exist. Natural
requests such as "use the three-agent ResearchForge panel" should activate it.

Do not use it for a quick factual lookup, a literature summary with no decision,
or a claim of patentability. Scientific novelty, commercial uniqueness, and
patentability remain separate questions.

## Prerequisites

- Hermes `delegate_task` must be enabled. Three initial children run in one
  batch, so `delegation.max_concurrent_children` must be at least 3. Current
  Hermes defaults to 10, although a profile can override it.
- Retrieval must be available through configured `web_search`, `web_extract`,
  `browser_exec`, scholarly MCP servers, or other permitted research tools.
- `terminal` is required only for deterministic score verification with
  `scripts/score.py`, `scripts/validate.py`, and optional dashboard publishing.
- A configured dashboard uses `RESEARCHFORGE_SITE_URL` and
  `RESEARCHFORGE_SITE_TOKEN`. Keep the token in the Gateway environment; never
  place it in a prompt, report, source file, Telegram message, or child task.
- Telegram is only the conversation surface. Install this skill in the active
  profile on the server that runs the Hermes gateway.

If a tool or database is unavailable, continue with a provisional assessment
and record the coverage gap. Never repeatedly retry a blocked source.

## How to Run

From Telegram or any Hermes chat, the exact prefix `Assess Research idea:` is
the user's standing trigger for the complete workflow below: assessment,
validation, and one private dashboard publication when publisher credentials
are configured. This trigger authorizes private publication without a separate
confirmation; keep the report private and never make it public unless the user
explicitly asks. If the user says not to publish, follow that instruction.

Example:

```text
Assess Research idea:
<idea>
```

For a non-publishing assessment, the user should say so explicitly, e.g.:

```text
Assess Research idea, but do not publish:
<idea>
```

The parent conversation is the Director. It must read these linked files before
delegating:

- `references/theorist.md`
- `references/challenger.md`
- `references/arbiter.md`
- `references/evidence-policy.md`
- `references/output-contract.md`

## Quick Reference

| Role | Deliberate preference | Initial budget | Required contribution |
|---|---|---:|---|
| Theorist | Explore defensible new contributions | 8 searches | Gaps, hypotheses, alternatives |
| Challenger | Minimize false novelty claims | 10 searches | Closest prior art and counterevidence |
| Arbiter | Minimize unsupported decisions | 4 searches | Independent baseline and audit plan |

The three initial roles start together. The Arbiter's initial run is a baseline,
not the final verdict. After the Director exposes the frozen Theorist and
Challenger results, a final Arbiter run adjudicates their disagreements.

## Procedure

### 1. Freeze the idea snapshot

Assign an `idea_id` and `idea_version`. Use only the idea text in the current
`Assess Research idea:` message as `original_idea`; never append or reuse
wording from earlier sessions, reports, or prior versions unless the user
explicitly asks to continue that version. Preserve the wording exactly, then
normalize it into separate fields. Put interpretations in `proposed_contribution`
or `assumptions`, clearly labeled as analysis rather than user input.

Separate user-supplied facts from working assumptions. Ask a question only when
the missing answer would materially change the search or decision.

Write the snapshot to a unique run-specific JSON file before delegating. Compare
`original_idea` byte-for-byte with the current message, and pass that exact text
to every role, including the final Arbiter; a normalized question is additional
analysis, never a substitute. Before reusing any artifact, verify its embedded
`idea_id`, `idea_version`, and original text match this snapshot—topic similarity
or a plausible filename is not enough.

Done when all children can inspect the same immutable snapshot without guessing
the central claim.

### 2. Launch all three roles in one batch

Make one `delegate_task(tasks=[...])` call containing exactly three leaf tasks.
Give every child the same snapshot and evidence policy, but different role
instructions:

1. **Theorist** — load `references/theorist.md` and
   `references/output-contract.md` with `skill_view`. Return an independent
   assessment without seeing the other roles.
2. **Challenger** — load `references/challenger.md` and
   `references/output-contract.md`. Try to defeat the novelty claim under other
   terminology and in other disciplines.
3. **Arbiter baseline** — load `references/arbiter.md` and
   `references/output-contract.md`. Produce an independent score, a list of
   decisive claims to verify, and abstention conditions. Do not predict what the
   other agents will say.

Use one batch call rather than three separate calls. Set every child to `leaf`;
children must not delegate further. Require structured JSON in fenced output,
followed by a short human-readable summary.

Done when three independently produced results refer to the same idea version.

#### Recovering a failed initial role

If a child fails after starting, inspect its completed failure record to count any searches and recover only that child's own partial sources/results. After a transient provider cooldown, retry only the failed role with the same frozen idea and no new searches by default; never expose sibling findings to an initial role. If a structured result cannot be recovered, mark that role incomplete and do not claim all three completed.

### 3. Enforce the shared search budget

Apply these rules to every role and to the Director:

- Never issue the same normalized query twice.
- When reassessing the same idea, check the prior run's search_log before
  searching; if it is unavailable, disclose that gap and do not claim
  query-level non-repetition across runs.
- Maintain one Director-owned search ledger and count every `web_search` call by children, the Director, and retries, including failed calls and calls made by children that later fail.
- Before final arbitration and publication, reconcile the cumulative count and exact queries with the tool outputs, then pass the complete ledger to the final Arbiter. Any later Director search must update the ledger and final report; never freeze the budget from child counts alone.
- If a recovered role lacks exact query strings or result counts, preserve the known call count, disclose the missing metadata, and never invent query logs or result counts.
- For the `Assess Research idea:` workflow, enforce a hard cap of 12 total
  searches across all initial roles, Director searches, rebuttal, and final
  Arbiter; per-role ceilings do not increase this global limit.
- Stop after two consecutive failures from the same tool or provider.
- Do not retry a blocked page with cosmetic query changes.
- Prefer inspected primary sources over search snippets.
- When a database fails, record it as a coverage gap and move on.
- Return a provisional result when the budget expires.

Initial caps are 8 searches for the Theorist, 10 for the Challenger, and 4 for
the Arbiter. These are per-role ceilings, not targets; the automated
`Assess Research idea:` workflow also enforces a hard global maximum of 12
searches across the full run, including Director-side searches, rebuttal, and
final-Arbiter searches. A child that has enough decisive evidence should stop early.

Done when no role can enter an unbounded retrieval loop.

### 4. Merge evidence and expose disagreements

Parse the three results. Reject invented URLs and sources that were not
retrieved. Deduplicate sources by DOI, stable identifier, or canonical URL.
As each completion result arrives, persist its complete structured JSON
immediately to a run-specific file such as `<idea_id>-<role>.json` before
starting final arbitration; delegation logs and summaries may be truncated and
are not substitutes for the returned JSON. Confirm each artifact parses, has the
expected role and idea version, and contains all criterion tables. Never reuse
an existing artifact because its topic or filename looks relevant. Only merge
outputs after the delegated unit has reported completion; files or transcripts
from a running child are intermediate and not authoritative. If the completion
output and an artifact conflict, stop and reconcile the final result before
building or publishing the payload. Never reconstruct missing criterion ratings
from aggregate RNI/EAS scores; keep missingness explicit or stop to recover the
raw result. Follow decisive
bibliography leads to the primary source before scoring; a citation mention is
a discovery lead, not verified evidence. Keep role-specific evidence IDs while
building a crosswalk.

Create a disagreement table with:

- claim;
- Theorist position and evidence;
- Challenger position and evidence;
- Arbiter baseline position;
- relationship to prior work: equivalent, direct overlap, partial overlap,
  transferable method, analogy only, or superficial similarity;
- fact or search that could change the decision.

Do not average scores or vote. Treat every role as potentially mistaken.

Done when every material disagreement is claim-level and evidence-linked.

### 5. Run at most one targeted rebuttal round

Only run a rebuttal when a disagreement could change the verdict. Batch the
Theorist and Challenger together again, showing each the frozen opposing claim
and its evidence. Each may make at most four new searches and must either add a
new source, analyze a changed assumption, or explicitly concede.

Skip this phase when no decisive disagreement remains. Never run a general
second literature search and never exceed one rebuttal round.

Done when the disagreement is resolved, narrowed, or explicitly left open.

### 6. Ask the Arbiter for the final decision

Make one final `delegate_task` call to the Arbiter. Supply the exact verbatim
frozen snapshot (not a paraphrase alone), all persisted initial role JSON, the
current Director-owned search ledger with cumulative count, the disagreement
table, any rebuttals, and the merged evidence ledger. The final Arbiter may use
at most four targeted searches to check decisive claims; record and reconcile
any such calls before validation.

Require the Arbiter to:

- verify decisive evidence rather than trust either role;
- check whether decisive preprints have a published journal version; deduplicate versions of the same work and do not count them as independent corroboration;
- independently rate every novelty and evidence-adequacy criterion;
- distinguish research value from novelty;
- choose `provisional`, `needs_human_review`, `already_addressed`, `approved`,
  or `rejected`;
- state what evidence could reverse the verdict;
- identify the smallest next experiment, proof, or comparison.

Done when the verdict is traceable to evidence and unresolved uncertainty is
visible.

### 7. Verify arithmetic deterministically

The LLM supplies criterion ratings and rationales; trusted code computes totals.
Write the final assessment JSON to a task file, then run the packaged verifier
through `terminal` using the active skill directory:

```text
python $HERMES_HOME/skills/researchforge-panel/scripts/validate.py final_decision.json
```

On native Windows use the equivalent path under
`%HERMES_HOME%\skills\researchforge-panel\scripts\validate.py`.

If verification fails, correct the JSON or arithmetic. Do not silently replace
missing evidence with empty identifiers.

Done when RNI and EAS match the packaged rubric calculation.

### 8. Build and publish the dashboard payload

Create one JSON object that conforms to
`templates/schemas/dashboard_payload.schema.json`. It must contain the frozen
idea, Theorist assessment, Challenger assessment, bounded debate, final Arbiter
decision, merged evidence bundle, and any proposed projects. Do not publish raw
chain-of-thought, API credentials, private reviewer details, or sources that
were not actually retrieved.

Before posting, validate the full payload against the dashboard schema. The
current `validate.py --publish-dashboard` path checks only that top-level
`idea` and `arbiter` keys exist; it does not validate the full schema. If a
required role field is missing, do not fill it with guessed values. Pause for
the raw result or use an explicitly supported missing-value representation.

Write it to a task-local file such as `dashboard_payload.json`. When both
dashboard environment variables are available, publish it once:

```text
python $HERMES_HOME/skills/researchforge-panel/scripts/validate.py --publish-dashboard dashboard_payload.json
```

The script prints a JSON object containing the stable `url`. Capture that URL
and include it in the Telegram answer. Do not call the publisher more than once
for the same run. After posting, read back the exact report URL in an authenticated browser. If
the page requires sign-in, use only an already authorized session or an approved
vault flow; never guess credentials or request passwords in chat. If no
authenticated session is available, stop at the sign-in page, report that the
API accepted the payload but rendering was not verified, and ask the user to
open the link while signed in. Do not republish just to test access. If publishing fails,
record the error briefly, keep the local JSON, and still return the scientific
result; do not retry repeatedly.

Done when the visual report is available or the publishing limitation is
explicitly stated.

### 9. Return a Telegram-sized result

Telegram receives a concise decision, not the entire agent transcript:

1. verdict and one-paragraph rationale;
2. Research Novelty Index (RNI) and Evidence Adequacy Score (EAS), explicitly
   described as rubric indices rather than probabilities;
3. strongest case for the idea;
4. strongest case against it;
5. closest prior work with links;
6. unresolved questions and coverage gaps;
7. next discriminating experiment;
8. where the three roles agreed and disagreed.

When publishing succeeds, end with one Markdown link:

```text
Open the visual ResearchForge report: <secure report URL>
```

Do not paste the full structured report into Telegram. When no publisher is
configured, save the structured JSON and offer it as a file without inventing
a link.

Done when the user can understand the decision in Telegram and audit it from
the attached evidence.

## Pitfalls

- Installing the original blueprint's 34 nested skills as unrelated top-level
  skills; this loses the three role system instructions and routing contract.
- Launching the final Arbiter before the independent results are frozen.
- Calling all three results a consensus because their numerical scores are
  close.
- Letting one child consume the entire search budget or repeatedly query a
  failing provider.
- Treating a new dataset, location, or model substitution as scientific novelty
  without a new insight.
- Claiming an absent search result proves that no prior work exists.
- Publishing an unpublished research proposal through a public, indexable URL.
- Leaking `RESEARCHFORGE_SITE_TOKEN` into a prompt, child task, log excerpt, or
  Telegram reply.

## Verification

Before completing a run, confirm that:

- one batch launched three independent initial roles;
- the frozen original text exactly matches the current user's idea and every artifact uses the same `idea_id` and `idea_version`;
- no role exceeded its tool budget or repeated a failed query, and the global search ledger includes Director-side searches;
- sources are retrievable, deduplicated, and linked to claims;
- no more than one targeted rebuttal round occurred;
- the final Arbiter received the verbatim idea, full frozen role outputs, and current search ledger, and did not average scores;
- `scripts/validate.py` accepted the final JSON and the complete dashboard payload passed its full schema;
- the dashboard payload was published at most once and its URL was captured;
- RNI, EAS, research value, commercial uniqueness, and patentability are not
  conflated;
- the Telegram reply labels limitations and does not claim certified novelty.

