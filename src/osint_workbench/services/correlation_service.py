from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _normalize_value(item_type: str, value: object) -> str:
    raw = str(value or "").strip()
    kind = str(item_type or "").upper()
    if kind == "DOMAIN":
        return raw.rstrip(".").lower()
    if kind in {"EMAIL", "USERNAME", "SERVICE_SIGNAL", "HOST"}:
        return raw.lower()
    if kind in {"PROFILE", "PROFILE_CANDIDATE", "URL"}:
        try:
            parts = urlsplit(raw)
            if parts.scheme and parts.netloc:
                return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, parts.fragment))
        except Exception:
            pass
    return raw


def canonical_evidence_key(item: dict) -> str | None:
    kind = str(item.get("type") or "").strip().upper()
    value = _normalize_value(kind, item.get("value"))
    if not kind or not value:
        return None
    return f"{kind}:{value}"


def _case_snapshot(case: Path) -> dict | None:
    meta = _read_json(case / "meta.json", {})
    if not meta:
        return None
    evidence = _read_json(case / "evidence.json", [])
    keys: dict[str, dict] = {}
    for item in evidence if isinstance(evidence, list) else []:
        key = canonical_evidence_key(item)
        if key:
            keys[key] = item
    return {
        "case_id": str(meta.get("case_id") or case.name),
        "target": str(meta.get("target") or meta.get("email") or meta.get("username") or ""),
        "type": str(meta.get("type") or ""),
        "status": str(meta.get("status") or ""),
        "evidence": evidence if isinstance(evidence, list) else [],
        "keys": keys,
    }


def _snapshots(root: str | Path) -> list[dict]:
    base = Path(root)
    if not base.is_dir():
        return []
    result = []
    for case in sorted((p for p in base.iterdir() if p.is_dir()), key=lambda p: p.name, reverse=True):
        snapshot = _case_snapshot(case)
        if snapshot:
            result.append(snapshot)
    return result


def related_cases(case_id: str, root: str | Path, *, limit: int = 20) -> list[dict]:
    all_cases = _snapshots(root)
    current = next((item for item in all_cases if item["case_id"] == case_id), None)
    if current is None:
        raise FileNotFoundError(case_id)
    current_keys = set(current["keys"])
    result = []
    for other in all_cases:
        if other["case_id"] == case_id:
            continue
        shared_keys = sorted(current_keys & set(other["keys"]))
        if not shared_keys:
            continue
        shared = []
        for key in shared_keys:
            item = current["keys"].get(key) or other["keys"].get(key) or {}
            shared.append({"key": key, "type": item.get("type", ""), "value": item.get("value", "")})
        result.append({
            "case_id": other["case_id"],
            "target": other["target"],
            "type": other["type"],
            "status": other["status"],
            "shared_count": len(shared),
            "shared": shared,
        })
    result.sort(key=lambda x: (-x["shared_count"], x["case_id"]), reverse=False)
    return result[: max(1, min(int(limit), 100))]


def search_cases(query: str, root: str | Path, *, limit: int = 50) -> list[dict]:
    needle = str(query or "").strip().lower()
    if not needle:
        return []
    matches = []
    for item in _snapshots(root):
        meta_hit = needle in item["case_id"].lower() or needle in item["target"].lower() or needle in item["type"].lower()
        evidence_hits = []
        for evidence in item["evidence"]:
            haystack = " ".join([
                str(evidence.get("type") or ""),
                str(evidence.get("value") or ""),
                " ".join(str(x) for x in (evidence.get("sources") or [])),
            ]).lower()
            if needle in haystack:
                evidence_hits.append({"type": evidence.get("type", ""), "value": evidence.get("value", "")})
        if meta_hit or evidence_hits:
            matches.append({
                "case_id": item["case_id"],
                "target": item["target"],
                "type": item["type"],
                "status": item["status"],
                "match_count": (1 if meta_hit else 0) + len(evidence_hits),
                "evidence_matches": evidence_hits[:10],
            })
    matches.sort(key=lambda x: (-x["match_count"], x["case_id"]))
    return matches[: max(1, min(int(limit), 100))]
