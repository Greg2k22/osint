# OSINT Workbench v2.3 Pivot Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic PASSIVE pivot planning, queueing, provenance and investigation-path UI/reporting.

**Architecture:** A pure-Python pivot service reads CASE bundles and current jobs, scores evidence-derived pivots and exposes safe queue operations through a dedicated FastAPI router. Provenance is stored with job metadata and in the parent CASE lineage file; UI and reports read this local state.

**Tech Stack:** Python/FastAPI, JSON CASE/job bundles, pytest, vanilla JS, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-09-04-v23-pivot-engine-design.md`

## Global Constraints
- No ACTIVE auto-pivoting.
- No new collectors.
- Do not weaken existing ACTIVE token guard.
- Do not mutate evidence files during pivot discovery.
- Max pivot depth 3; max automatic batch 10.
- Preserve v2.2 API compatibility.

### Task 1: Pivot domain tests
- [ ] Add failing tests for mapping, score, deduplication, depth and provenance.
- [ ] Run v2.3 tests and verify RED.

### Task 2: Pivot service and queue
- [ ] Implement deterministic pivot proposals.
- [ ] Implement PASSIVE enqueue and lineage persistence.
- [ ] Prevent duplicate/self/existing-target loops.

### Task 3: API and reports
- [ ] Add pivot GET/enqueue/auto-enqueue endpoints.
- [ ] Add deterministic pivot summary and lineage to reports.

### Task 4: UI
- [ ] Add investigation-path/pivot panel.
- [ ] Add PASSIVE auto-enqueue button with explicit user action.

### Task 5: Verification and delivery
- [ ] Run full tests, compile, JS syntax, Compose config, build/runtime health.
- [ ] Push branch and create PR without merging.
