from __future__ import annotations

import hashlib
import json
import re
import uuid
from pathlib import Path
from urllib.parse import urlsplit

from osint_workbench.services.source_quality import source_families

MAX_DEPTH = 3
MAX_AUTO_BATCH = 10

BASE_SCORE = {
    "DOMAIN": 40,
    "EMAIL": 40,
    "USERNAME": 35,
    "PROFILE": 25,
    "PROFILE_CANDIDATE": 25,
    "HOST": 30,
    "IP": 20,
    "ORGANIZATION": 15,
}
CONFIDENCE_BONUS = {"HIGH": 30, "MEDIUM": 20, "LOW": 10, "SEED": 0}


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _norm_domain(value: str) -> str:
    return value.strip().rstrip(".").lower()


def _username_from_profile(value: str) -> str | None:
    try:
        parts = urlsplit(value.strip())
        if not parts.scheme or not parts.netloc:
            return None
        segments = [x for x in parts.path.split("/") if x]
        if not segments:
            return None
        candidate = segments[-1].strip().lower()
        if not re.fullmatch(r"[a-z0-9_.-]{1,100}", candidate):
            return None
        return candidate
    except Exception:
        return None


def pivot_target_from_evidence(item: dict) -> tuple[str, str] | None:
    kind = str(item.get("type") or "").strip().upper()
    raw = str(item.get("value") or "").strip()
    if not raw:
        return None
    if kind in {"DOMAIN", "HOST"}:
        target = _norm_domain(raw)
        if not target or " " in target or "." not in target:
            return None
        return "DOMAIN", target
    if kind == "EMAIL":
        target = raw.lower()
        if target.count("@") != 1:
            return None
        return "EMAIL", target
    if kind == "USERNAME":
        target = raw.lower()
        if not re.fullmatch(r"[a-z0-9_.-]{1,100}", target):
            return None
        return "PERSON", target
    if kind in {"PROFILE", "PROFILE_CANDIDATE"}:
        username = _username_from_profile(raw)
        return ("PERSON", username) if username else None
    return None


def _canonical_key(item: dict) -> str:
    kind = str(item.get("type") or "").strip().upper()
    value = str(item.get("value") or "").strip()
    return f"{kind}:{value.lower()}"


def _existing_targets(cases_root: Path, jobs_root: Path) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    if cases_root.is_dir():
        for case in cases_root.iterdir():
            if not case.is_dir():
                continue
            meta = _read_json(case / "meta.json", {})
            scan_type = str(meta.get("type") or "").strip().upper()
            target = str(meta.get("target") or meta.get("email") or meta.get("username") or "").strip().lower()
            if scan_type and target:
                if scan_type == "PERSON":
                    result.add(("PERSON", target))
                elif scan_type in {"DOMAIN", "EMAIL"}:
                    result.add((scan_type, target))
    for queue in ("pending", "running", "done", "failed"):
        folder = jobs_root / queue
        if not folder.is_dir():
            continue
        for path in folder.glob("*.json"):
            job = _read_json(path, {})
            scan_type = str(job.get("type") or "").strip().upper()
            target = str(job.get("target") or "").strip().lower()
            if scan_type and target:
                result.add((scan_type, target))
    return result


def _score(item: dict) -> int:
    kind = str(item.get("type") or "").strip().upper()
    confidence = str(item.get("confidence") or "LOW").strip().upper()
    sources = item.get("sources") or ([item.get("source")] if item.get("source") else [])
    families = source_families([str(x) for x in sources])
    return min(100, BASE_SCORE.get(kind, 10) + CONFIDENCE_BONUS.get(confidence, 0) + min(20, len(families) * 10))


def _pivot_id(case_id: str, evidence_key: str, scan_type: str, target: str, depth: int) -> str:
    raw = f"{case_id}|{evidence_key}|{scan_type}|{target}|{depth}".encode()
    return hashlib.sha256(raw).hexdigest()[:20]


def build_pivot_plan(case_id: str, cases_root: str | Path, jobs_root: str | Path, *, max_depth: int = 2, limit: int = 50) -> dict:
    cases_root = Path(cases_root)
    jobs_root = Path(jobs_root)
    case = cases_root / case_id
    meta = _read_json(case / "meta.json", {})
    if not meta:
        raise FileNotFoundError(case_id)
    evidence = _read_json(case / "evidence.json", [])
    current_target = str(meta.get("target") or meta.get("email") or meta.get("username") or "").strip().lower()
    current_type = str(meta.get("type") or "").strip().upper()
    current_depth = int(meta.get("pivot_depth") or 0)
    requested_max_depth = max(0, min(int(max_depth), MAX_DEPTH))
    next_depth = current_depth + 1
    depth_limit_reached = next_depth > requested_max_depth or next_depth > MAX_DEPTH
    existing = _existing_targets(cases_root, jobs_root)
    seen: set[tuple[str, str]] = set()
    pivots = []

    for item in evidence if isinstance(evidence, list) else []:
        mapped = pivot_target_from_evidence(item)
        kind = str(item.get("type") or "").strip().upper()
        value = str(item.get("value") or "").strip()
        evidence_key = _canonical_key(item)
        score = _score(item)
        families = sorted(source_families([str(x) for x in (item.get("sources") or [])]))
        if mapped is None:
            if kind in {"IP", "ORGANIZATION"}:
                pivots.append({
                    "pivot_id": _pivot_id(case_id, evidence_key, "MANUAL", value, next_depth),
                    "parent_case_id": case_id,
                    "evidence_key": evidence_key,
                    "evidence_type": kind,
                    "evidence_value": value,
                    "scan_type": None,
                    "target": value,
                    "score": score,
                    "confidence": str(item.get("confidence") or "LOW").upper(),
                    "source_families": families,
                    "depth": next_depth,
                    "reason": f"{kind} evidence requires a dedicated/manual pivot",
                    "executable": False,
                    "active": False,
                    "blocked_reason": "unsupported_scan_type",
                })
            continue
        scan_type, target = mapped
        pair = (scan_type, target)
        if pair in seen:
            continue
        seen.add(pair)
        self_target = target == current_target and (scan_type == current_type or current_type == "PERSON")
        blocked = None
        if self_target:
            blocked = "self_target"
        elif pair in existing:
            blocked = "already_known"
        elif depth_limit_reached:
            blocked = "depth_limit"
        pivots.append({
            "pivot_id": _pivot_id(case_id, evidence_key, scan_type, target, next_depth),
            "parent_case_id": case_id,
            "evidence_key": evidence_key,
            "evidence_type": kind,
            "evidence_value": value,
            "scan_type": scan_type,
            "target": target,
            "score": score,
            "confidence": str(item.get("confidence") or "LOW").upper(),
            "source_families": families,
            "depth": next_depth,
            "reason": f"{kind} evidence can be investigated as {scan_type}",
            "executable": blocked is None,
            "active": False,
            "blocked_reason": blocked,
        })

    pivots.sort(key=lambda p: (-int(p["score"]), str(p.get("target") or ""), str(p["pivot_id"])))
    limit = max(1, min(int(limit), 100))
    return {
        "case_id": case_id,
        "current_depth": current_depth,
        "next_depth": next_depth,
        "max_depth": requested_max_depth,
        "depth_limit_reached": depth_limit_reached,
        "pivots": pivots[:limit],
    }


def _append_lineage(case: Path, entry: dict) -> None:
    path = case / "pivot_lineage.json"
    value = _read_json(path, [])
    if not isinstance(value, list):
        value = []
    value.append(entry)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def enqueue_pivot(case_id: str, pivot_id: str, cases_root: str | Path, jobs_root: str | Path) -> dict:
    cases_root = Path(cases_root)
    jobs_root = Path(jobs_root)
    plan = build_pivot_plan(case_id, cases_root, jobs_root, max_depth=MAX_DEPTH, limit=100)
    pivot = next((p for p in plan["pivots"] if p["pivot_id"] == pivot_id), None)
    if pivot is None:
        raise KeyError(pivot_id)
    if not pivot["executable"]:
        raise ValueError(pivot.get("blocked_reason") or "pivot_not_executable")
    pending = jobs_root / "pending"
    pending.mkdir(parents=True, exist_ok=True)
    job_id = uuid.uuid4().hex
    payload = {
        "id": job_id,
        "type": pivot["scan_type"],
        "target": pivot["target"],
        "active": False,
        "authorized": False,
        "status": "PENDING",
        "origin": "PIVOT",
        "pivot_id": pivot["pivot_id"],
        "pivot_parent_case_id": case_id,
        "pivot_parent_evidence_key": pivot["evidence_key"],
        "pivot_depth": pivot["depth"],
        "pivot_score": pivot["score"],
        "pivot_reason": pivot["reason"],
    }
    tmp = pending / f".{job_id}.tmp"
    dst = pending / f"{job_id}.json"
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(dst)
    lineage = {
        "job_id": job_id,
        "pivot_id": pivot["pivot_id"],
        "scan_type": pivot["scan_type"],
        "target": pivot["target"],
        "depth": pivot["depth"],
        "score": pivot["score"],
        "reason": pivot["reason"],
        "evidence_key": pivot["evidence_key"],
        "active": False,
        "status": "PENDING",
    }
    _append_lineage(cases_root / case_id, lineage)
    return {"job_id": job_id, **lineage}


def auto_enqueue(case_id: str, cases_root: str | Path, jobs_root: str | Path, *, min_score: int = 60, max_count: int = 5, max_depth: int = 2) -> list[dict]:
    max_count = max(1, min(int(max_count), MAX_AUTO_BATCH))
    min_score = max(0, min(int(min_score), 100))
    plan = build_pivot_plan(case_id, cases_root, jobs_root, max_depth=max_depth, limit=100)
    result = []
    for pivot in plan["pivots"]:
        if len(result) >= max_count:
            break
        if not pivot["executable"] or int(pivot["score"]) < min_score:
            continue
        result.append(enqueue_pivot(case_id, pivot["pivot_id"], cases_root, jobs_root))
    return result
