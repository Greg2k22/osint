from __future__ import annotations

SOURCE_FAMILY = {
    "sherlock": "account-discovery",
    "maigret": "account-discovery",
    "holehe": "email-registration",
    "subfinder": "dns-discovery",
    "theharvester": "dns-discovery",
    "bbot": "attack-surface",
    "httpx": "web-probing",
}


def source_families(sources: list[str] | tuple[str, ...] | None) -> list[str]:
    families = {
        SOURCE_FAMILY.get(str(source).strip().lower(), f"source:{str(source).strip().lower()}")
        for source in (sources or [])
        if str(source).strip()
    }
    return sorted(families)


def annotate_evidence(evidence: list[dict]) -> list[dict]:
    result = []
    for item in evidence:
        families = source_families(item.get("sources") or ([item.get("source")] if item.get("source") else []))
        result.append({
            **item,
            "source_families": families,
            "independent_source_count": len(families),
        })
    return result
