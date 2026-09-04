from collections import defaultdict

from ..scoring import confidence_for, independent_source_groups


def normalize_email_records(email: str, records: list[dict]) -> list[dict]:
    email = str(email).strip().lower()
    grouped: dict[str, dict] = {}
    sources: dict[str, set[str]] = defaultdict(set)

    for record in records:
        if str(record.get("status", "")).upper() != "FOUND":
            continue
        service = str(record.get("service", "")).strip()
        source = str(record.get("source", "")).strip().lower()
        if not service or not source:
            continue
        key = service.casefold()
        grouped.setdefault(key, {"service": service})
        sources[key].add(source)

    result = []
    for key in sorted(grouped):
        raw_sources = sorted(sources[key])
        independent = independent_source_groups(raw_sources)
        result.append({
            "type": "SERVICE_SIGNAL",
            "value": grouped[key]["service"],
            "email": email,
            "service": grouped[key]["service"],
            "status": "FOUND",
            "sources": raw_sources,
            "source": raw_sources[0],
            "independent_sources": sorted(independent),
            "confidence": confidence_for(independent),
        })
    return result
