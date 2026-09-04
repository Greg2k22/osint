# OSINT Workbench v2.1 Maintenance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add CI, safe configuration examples, backup/restore tooling, and operational documentation.

**Architecture:** Maintenance features stay outside the core scan pipeline. CI performs static/config/test checks only; backup/restore uses existing Compose services; documentation defines safe operations.

**Tech Stack:** GitHub Actions, Bash, Docker Compose, Python/pytest, Node syntax check.

**Spec:** `docs/superpowers/specs/2026-09-04-v21-maintenance-design.md`

## Global Constraints
- Do not add collectors.
- Do not use `docker compose down -v` in executable scripts.
- Never commit real secrets, `.env`, runtime `data/`, or `backups/`.
- ACTIVE DOMAIN remains token-gated; PASSIVE remains default.

### Task 1: Maintenance contract tests
- [ ] Add failing tests for CI, env example, ignore rules, backup/restore safety and README.
- [ ] Run tests and verify RED.

### Task 2: CI and configuration
- [ ] Add `.github/workflows/ci.yml`.
- [ ] Add `.env.example` with placeholders only.
- [ ] Update `.gitignore`.

### Task 3: Backup and restore
- [ ] Add `scripts/backup.sh`.
- [ ] Add `scripts/restore.sh` with explicit source and confirmation.

### Task 4: Documentation
- [ ] Add README covering operations, safety, privacy and recovery.

### Task 5: Verification and delivery
- [ ] Run full tests/compile/Compose/JS/build/runtime checks.
- [ ] Verify secrets and ignored paths.
- [ ] Commit, push and create PR without merging.
