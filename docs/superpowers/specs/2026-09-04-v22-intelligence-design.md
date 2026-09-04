# OSINT Workbench v2.2 Intelligence Design

## Goal
Add a deterministic intelligence layer over existing collectors: cross-case correlation, source-family independence, case search, related-case discovery, and stronger reports/UI without adding external AI or weakening PASSIVE-by-default behavior.

## Design
- Correlation works on normalized evidence stored in local CASE bundles, not on raw collector output.
- Canonical keys are type-aware and case-insensitive for identifiers where appropriate.
- Related CASE ranking is based on shared canonical evidence keys, with shared items exposed for auditability.
- Source independence groups known collectors into source families so multiple observations from the same family are not counted as independent confirmations.
- Reports add deterministic executive summaries and source-group metrics; no LLM-generated claims.
- API adds local-only search and related-case endpoints.
- UI adds case search and a related-case panel.

## Constraints
- No new external collector images in v2.2.
- Existing collector behavior remains unchanged.
- PASSIVE stays default; ACTIVE remains DOMAIN-only and token-gated.
- No external AI or outbound analysis service.
- Existing API endpoints remain compatible.
- All new behavior must be covered by tests and CI.
