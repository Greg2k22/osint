#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from osint_workbench.services.case_service import write_case_bundle
from osint_workbench.services.normalizers.domain import normalize_domain_records
from osint_workbench.services.normalizers.email import normalize_email_records
from osint_workbench.services.normalizers.person import normalize_profile_records


def evidence_id(case_id: str, kind: str, value: str, source: str) -> str:
    raw = f"{case_id}|{kind}|{value}|{source}".encode()
    return "ev-" + hashlib.sha256(raw).hexdigest()[:16]


def evidence_for(case_id: str, records: list[dict]) -> list[dict]:
    out = []
    for item in records:
        for source in item.get("sources", []):
            if source in {"target", "seed"}:
                continue
            out.append({
                "id": evidence_id(case_id, item["type"], item["value"], source),
                "case_id": case_id,
                "type": item["type"],
                "value": item["value"],
                "source": source,
                "confidence": item["confidence"],
            })
    return out


def copy_raw(case: Path) -> None:
    raw_dir = case / "raw"
    raw_dir.mkdir(exist_ok=True)
    for pattern in ("*.txt", "*.log", "*.jsonl"):
        for source in case.glob(pattern):
            if source.name in {"hosts.txt", "profiles.txt", "services.txt"}:
                continue
            shutil.copy2(source, raw_dir / source.name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case")
    args = parser.parse_args()
    case = Path(args.case).resolve()
    case_id = case.name
    meta_path = case / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    if (case / "hosts.json").exists():
        legacy = json.loads((case / "hosts.json").read_text())
        target = next((x.get("host") for x in legacy if "target" in x.get("sources", [])), None)
        if not target:
            raise SystemExit("DOMAIN case has no target seed")
        source_records = []
        for item in legacy:
            for source in item.get("sources", []):
                source_records.append({"host": item.get("host"), "source": source, "resolved_ips": item.get("resolved_ips", [])})
        normalized = normalize_domain_records(target, source_records)
        (case / "hosts.json").write_text(json.dumps(normalized, indent=2, ensure_ascii=False) + "\n")
        case_type = "DOMAIN"
    elif (case / "profiles.json").exists():
        legacy = json.loads((case / "profiles.json").read_text())
        target = meta.get("target") or meta.get("username") or next((x.get("username") for x in legacy), None)
        source_records = [{"url": x.get("url"), "source": s} for x in legacy for s in x.get("sources", [])]
        normalized = normalize_profile_records(target or "", source_records)
        (case / "profiles.json").write_text(json.dumps(normalized, indent=2, ensure_ascii=False) + "\n")
        case_type = "PERSON"
    elif (case / "services.json").exists():
        legacy = json.loads((case / "services.json").read_text())
        target = meta.get("target") or meta.get("email") or next((x.get("email") for x in legacy), None)
        source_records = []
        for x in legacy:
            for source in x.get("sources", [x.get("source", "holehe")]):
                source_records.append({"service": x.get("service"), "source": source, "status": x.get("status", "FOUND")})
        normalized = normalize_email_records(target or "", source_records)
        (case / "services.json").write_text(json.dumps(normalized, indent=2, ensure_ascii=False) + "\n")
        case_type = "EMAIL"
    else:
        raise SystemExit("Unsupported CASE: no legacy normalized JSON")

    mode = meta.get("mode", "PASSIVE")
    new_meta = {
        **meta,
        "case_id": case_id,
        "type": case_type,
        "target": target,
        "mode": mode,
        "status": meta.get("status", "DONE"),
        "schema_version": 2,
    }
    write_case_bundle(case, meta=new_meta, normalized=normalized, evidence=evidence_for(case_id, normalized), findings=[])
    copy_raw(case)
    print(f"CASE v2: {case_id} ({len(normalized)} normalized records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
