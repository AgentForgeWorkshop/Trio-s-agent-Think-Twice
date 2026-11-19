#!/usr/bin/env python3
"""Deterministic ResearchForge RNI/EAS scoring.

Usage: python score.py final_decision.json [--json]
"""

import argparse
from decimal import Decimal
import json
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


class ScoringError(ValueError):
    pass


def load_rubric(kind):
    if kind not in {"novelty", "evidence_adequacy"}:
        raise ScoringError(f"Unknown rubric: {kind}")
    path = SKILL_ROOT / "templates" / f"{kind}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def score_rubric(criteria, kind="novelty"):
    rubric = load_rubric(kind)
    expected = {criterion["id"] for criterion in rubric["criteria"]}
    if not isinstance(criteria, dict) or set(criteria) != expected:
        actual = sorted(criteria) if isinstance(criteria, dict) else "not an object"
        raise ScoringError(f"Expected exactly {sorted(expected)}; got {actual}")
    total = Decimal("0")
    for criterion in rubric["criteria"]:
        entry = criteria[criterion["id"]]
        if not isinstance(entry, dict):
            raise ScoringError(f"{criterion['id']} must be an object")
        rating = entry.get("rating")
        if type(rating) is not int or not 0 <= rating <= 4:
            raise ScoringError(f"{criterion['id']} rating must be an integer from 0 to 4")
        if not isinstance(entry.get("rationale"), str) or not entry["rationale"].strip():
            raise ScoringError(f"{criterion['id']} requires a rationale")
        evidence_ids = entry.get("evidence_ids")
        if not isinstance(evidence_ids, list) or any(not isinstance(item, str) for item in evidence_ids):
            raise ScoringError(f"{criterion['id']} requires an evidence_ids array")
        total += Decimal(str(criterion["weight"])) * Decimal(rating) / Decimal(4)
    return float(total.quantize(Decimal("0.01")))


def verify_assessment_scores(data):
    if "novelty_criteria" not in data or "adequacy_criteria" not in data:
        raise ScoringError("Missing novelty_criteria or adequacy_criteria")
    computed = {
        "rni": score_rubric(data["novelty_criteria"], "novelty"),
        "eas": score_rubric(data["adequacy_criteria"], "evidence_adequacy"),
    }
    for key, value in computed.items():
        provided = data.get(key)
        if not isinstance(provided, (int, float)) or isinstance(provided, bool):
            raise ScoringError(f"{key} must be numeric")
        if abs(float(provided) - value) > 0.011:
            raise ScoringError(f"{key} mismatch: reported {provided}, calculated {value}")
    return computed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    data = json.loads(args.file.read_text(encoding="utf-8"))
    scores = verify_assessment_scores(data)
    if args.json:
        print(json.dumps({"idea_id": data.get("idea_id"), **scores, "status": data.get("status")}, indent=2))
    else:
        print(
            f"Idea: {data.get('idea_id', 'unknown')} | RNI: {scores['rni']}/100 | "
            f"EAS: {scores['eas']}/100 | status: {data.get('status', 'unknown')}"
        )
        print("RNI and EAS are rubric indices, not probabilities of global novelty.")


if __name__ == "__main__":
    try:
        main()
    except (ScoringError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERROR: {exc}")

