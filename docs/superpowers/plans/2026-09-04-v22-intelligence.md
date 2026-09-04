# OSINT Workbench v2.2 Intelligence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add cross-case intelligence, source-family scoring, deterministic reporting and UI discovery.

**Architecture:** New pure-Python services read existing CASE bundles and expose correlation/search through a focused API router. Reports consume source-family annotations. UI consumes the new endpoints without changing collector execution.

**Tech Stack:** Python/FastAPI, local JSON CASE bundles, pytest, vanilla JS, existing Docker Compose.

**Spec:** `docs/superpowers/specs/2026-09-04-v22-intelligence-design.md`

## Global Constraints
- Preserve all v2.1 behavior and tests.
- Do not add external AI.
- Do not add new collector images.
- Do not weaken ACTIVE authorization.
- Do not mutate existing CASE evidence during reads.

### Task 1: RED tests
- [ ] Add failing tests for canonicalization, correlation, source families, API, reports and UI markers.
- [ ] Run v2.2 tests and verify RED.

### Task 2: Correlation and source intelligence
- [ ] Implement source-family annotation.
- [ ] Implement case search and related-case ranking.

### Task 3: API and reports
- [ ] Add `/api/search` and `/api/cases/{case_id}/related`.
- [ ] Add deterministic executive summary and independent-source metrics.

### Task 4: UI
- [ ] Add case search input.
- [ ] Add related-case panel and loading logic.

### Task 5: Verification and delivery
- [ ] Run full tests, compile, JS syntax, Compose config, build/runtime health.
- [ ] Push branch and create PR without merging.
