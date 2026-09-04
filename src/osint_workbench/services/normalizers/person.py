from collections import defaultdict

from ..scoring import confidence_for, independent_source_groups


def normalize_profile_records(username: str, records: list[dict]) -> list[dict]:
    grouped: dict[str, set[str]] = defaultdict(set)
    display_url: dict[str, str] = {}
    for record in records:
        url = str(record.get("url", "")).strip()
        source = str(record.get("source", "")).strip().lower()
        if not url.startswith(("http://", "https://")) or not source:
            continue
        key = url.casefold()
        display_url.setdefault(key, url)
        grouped[key].add(source)

    result = []
    for key in sorted(grouped):
        sources = sorted(grouped[key])
        independent = independent_source_groups(sources)
        result.append({
            "type": "PROFILE_CANDIDATE",
            "value": display_url[key],
            "username": username,
            "url": display_url[key],
            "sources": sources,
            "independent_sources": sorted(independent),
            "confidence": confidence_for(independent),
        })
    return result
