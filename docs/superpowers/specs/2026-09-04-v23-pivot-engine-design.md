# OSINT Workbench v2.3 Pivot Engine Design

## Goal
Turn the workbench from a case viewer into a deterministic investigation engine that proposes and safely queues PASSIVE pivots between supported entity types while preserving provenance and preventing loops.

## Design
- Pivot discovery consumes existing normalized CASE evidence only; it never invents entities.
- Supported executable pivots are DOMAIN, EMAIL and PERSON because these are the current scan contracts.
- IP and ORGANIZATION observations remain visible as manual pivots until dedicated collectors exist.
- Every pivot carries provenance: parent CASE, canonical evidence key, evidence type/value, reason, confidence, score and depth.
- Automatic enqueue is PASSIVE-only, bounded by score, max count and depth, and deduplicated against existing CASE targets and queued/completed jobs.
- Enqueue writes the normal job JSON plus pivot provenance fields; the existing runner may ignore additional metadata safely.
- Parent CASE stores `pivot_lineage.json` so the investigation path remains auditable even before child CASE creation.
- No ACTIVE pivot is ever generated or automatically queued.

## Scoring
- Base value depends on evidence type.
- HIGH/MEDIUM/LOW confidence contributes decreasing bonuses.
- Independent source families increase score but are capped.
- Existing targets, self-targets, duplicates and unsupported entity types are never auto-enqueued.

## Constraints
- PASSIVE remains default.
- ACTIVE authorization is unchanged.
- No new collector images.
- No external AI.
- No real ACTIVE scan in tests or CI.
- Maximum auto-enqueue depth is 3.
- Maximum auto-enqueue batch is 10 jobs.
