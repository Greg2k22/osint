from collections.abc import Iterable

IGNORED_SOURCE_GROUPS = {"seed", "target"}


def source_group(source: str) -> str | None:
    value = str(source or "").strip().lower()
    if not value or value in IGNORED_SOURCE_GROUPS:
        return None
    if value.startswith("bbot:") or value == "bbot":
        return "bbot"
    return value


def independent_source_groups(sources: Iterable[str]) -> set[str]:
    return {group for source in sources if (group := source_group(source)) is not None}


def confidence_for(source_groups: set[str]) -> str:
    count = len(source_groups)
    if count >= 3:
        return "HIGH"
    if count == 2:
        return "MEDIUM"
    if count == 1:
        return "LOW"
    return "SEED"
