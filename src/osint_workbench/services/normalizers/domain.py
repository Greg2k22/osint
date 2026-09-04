from collections import defaultdict
from ipaddress import ip_address

from ..scoring import confidence_for, independent_source_groups


def _clean_domain(value: str) -> str:
    return str(value).strip().rstrip(".").lower()


def _in_scope(host: str, domain: str) -> bool:
    return host == domain or host.endswith("." + domain)


def normalize_domain_records(domain: str, records: list[dict]) -> list[dict]:
    domain = _clean_domain(domain)
    sources: dict[str, set[str]] = defaultdict(set)
    ips: dict[str, set[str]] = defaultdict(set)
    sources[domain].add("target")

    for record in records:
        host = _clean_domain(record.get("host", ""))
        if not host or not _in_scope(host, domain):
            continue
        source = str(record.get("source", "")).strip().lower()
        if source:
            sources[host].add(source)
        for raw_ip in record.get("resolved_ips", []) or []:
            try:
                ips[host].add(str(ip_address(str(raw_ip))))
            except ValueError:
                continue

    result = []
    for host in sorted(sources):
        raw_sources = sorted(sources[host])
        independent = independent_source_groups(raw_sources)
        result.append({
            "type": "DOMAIN" if host == domain else "HOST",
            "value": host,
            "host": host,
            "sources": raw_sources,
            "independent_sources": sorted(independent),
            "confidence": confidence_for(independent),
            "resolved_ips": sorted(ips[host]),
        })
    return result
