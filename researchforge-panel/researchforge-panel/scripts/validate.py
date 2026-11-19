#!/usr/bin/env python3
"""Validate a final ResearchForge decision with only the standard library.

Usage:
  python validate.py final_decision.json
  python validate.py --publish-dashboard dashboard_payload.json
"""

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from score import ScoringError, verify_assessment_scores


VALID_STATUS = {
    "provisional",
    "needs_human_review",
    "already_addressed",
    "approved",
    "rejected",
}


def validate(data):
    for field in ("idea_id", "idea_version", "role", "status", "summary"):
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    if data["role"] != "arbiter_final":
        raise ValueError("Final decision role must be arbiter_final")
    if data["status"] not in VALID_STATUS:
        raise ValueError(f"Unsupported status: {data['status']}")
    scores = verify_assessment_scores(data)
    sources = data.get("sources", [])
    evidence = data.get("evidence", [])
    if not isinstance(sources, list) or not isinstance(evidence, list):
        raise ValueError("sources and evidence must be arrays")
    source_ids = {item.get("source_id") for item in sources if isinstance(item, dict)}
    evidence_ids = {item.get("evidence_id") for item in evidence if isinstance(item, dict)}
    if None in source_ids or len(source_ids) != len(sources):
        raise ValueError("Sources require unique source_id values")
    if None in evidence_ids or len(evidence_ids) != len(evidence):
        raise ValueError("Evidence records require unique evidence_id values")
    for item in evidence:
        if item.get("source_id") not in source_ids:
            raise ValueError(f"Evidence points to unknown source: {item.get('source_id')}")
    for table_name in ("novelty_criteria", "adequacy_criteria"):
        for row in data[table_name].values():
            unknown = set(row.get("evidence_ids", [])) - evidence_ids
            if unknown:
                raise ValueError(f"Criterion points to unknown evidence: {sorted(unknown)}")
    if data["status"] == "approved":
        if scores["eas"] == 0:
            raise ValueError("An approved decision cannot have zero EAS")
        if not any(item.get("verified") for item in evidence):
            raise ValueError("An approved decision requires verified evidence")
    if data["status"] == "already_addressed" and not data.get("decisive_prior_work"):
        raise ValueError("An already_addressed decision requires decisive_prior_work")
    return scores


def publish_dashboard(data):
    site_url = os.environ.get("RESEARCHFORGE_SITE_URL", "").rstrip("/")
    token = os.environ.get("RESEARCHFORGE_SITE_TOKEN", "")
    if not site_url or not token:
        raise ValueError("dashboard publisher is not configured")
    if not isinstance(data, dict) or "idea" not in data or "arbiter" not in data:
        raise ValueError("dashboard payload must contain idea and arbiter")
    request = urllib.request.Request(
        f"{site_url}/api/reports",
        data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token}",
            "User-Agent": "ResearchForge-Hermes/0.3",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read(500).decode("utf-8", errors="replace")
        raise ValueError(f"publisher HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ValueError(f"publisher request failed: {exc}") from exc
    url = result.get("url") if isinstance(result, dict) else None
    if not isinstance(url, str) or not url.startswith("https://"):
        raise ValueError("publisher returned no valid report URL")
    print(json.dumps({"ok": True, "url": url}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish-dashboard", action="store_true")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    data = json.loads(args.file.read_text(encoding="utf-8"))
    if args.publish_dashboard:
        publish_dashboard(data)
        return
    scores = validate(data)
    print(
        f"VALID: {args.file} [{data['idea_id']}] "
        f"RNI={scores['rni']}/100 EAS={scores['eas']}/100"
    )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, ScoringError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"INVALID: {exc}")

