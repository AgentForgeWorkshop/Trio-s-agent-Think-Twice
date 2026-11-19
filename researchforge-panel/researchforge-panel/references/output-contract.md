# ResearchForge Output Contract

Each role returns one JSON object in a fenced block plus a short prose summary.
The Director may add fields, but must preserve these relationships.

```json
{
  "idea_id": "RF-...",
  "idea_version": 1,
  "run_id": "...",
  "role": "theorist|challenger|arbiter_baseline|arbiter_final",
  "status": "provisional|needs_human_review|already_addressed|approved|rejected",
  "summary": "...",
  "claims": [
    {
      "claim_id": "...",
      "text": "...",
      "kind": "fact|hypothesis|novelty_claim|counterclaim",
      "supporting_evidence_ids": [],
      "contradicting_evidence_ids": [],
      "confidence": "low|moderate|high"
    }
  ],
  "sources": [
    {
      "source_id": "...",
      "title": "...",
      "locator": "https://...",
      "source_type": "paper|preprint|patent|product|software|report|other",
      "retrieved_at": "ISO-8601",
      "access_depth": "snippet|metadata|abstract|full_text|direct_evidence",
      "verified": false,
      "limitations": "..."
    }
  ],
  "evidence": [
    {
      "evidence_id": "...",
      "source_id": "...",
      "supports_claim_ids": [],
      "contradicts_claim_ids": [],
      "extract_or_summary": "...",
      "verified": false
    }
  ],
  "search_log": [
    {
      "engine": "...",
      "query": "...",
      "retrieved_at": "ISO-8601",
      "result_count": 0,
      "limitations": "..."
    }
  ],
  "novelty_criteria": {
    "N1": {"rating": 0, "rationale": "...", "evidence_ids": []},
    "N2": {"rating": 0, "rationale": "...", "evidence_ids": []},
    "N3": {"rating": 0, "rationale": "...", "evidence_ids": []},
    "N4": {"rating": 0, "rationale": "...", "evidence_ids": []},
    "N5": {"rating": 0, "rationale": "...", "evidence_ids": []}
  },
  "adequacy_criteria": {
    "E1": {"rating": 0, "rationale": "...", "evidence_ids": []},
    "E2": {"rating": 0, "rationale": "...", "evidence_ids": []},
    "E3": {"rating": 0, "rationale": "...", "evidence_ids": []},
    "E4": {"rating": 0, "rationale": "...", "evidence_ids": []},
    "E5": {"rating": 0, "rationale": "...", "evidence_ids": []}
  },
  "rni": 0,
  "eas": 0,
  "strongest_case_for": "...",
  "strongest_case_against": "...",
  "coverage_gaps": [],
  "next_experiment": "...",
  "reversal_conditions": []
}
```

The final Arbiter object is the score-verification input. All criteria must be
present. Ratings are integers from 0 through 4. Evidence identifiers must refer
to records in the merged evidence bundle used by the final decision.

