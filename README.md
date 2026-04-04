# SPOOLER

## Ephemeral Environment Orchestrator for Generated Code

### Fast, reproducible, hostile environment packaging for QA workflows

---

## GitHub Repository Description (Copy/Paste)

Build hostile, reproducible test environments for generated code in under a minute using presets, challenge levels, and injectable payload files.

---

## Executive Summary

SPOOLER is a Streamlit-based environment builder that creates a reproducible Docker Compose recipe plus injection artifacts from a lightweight UI.

It is designed for a practical pain point: teams can generate code quickly, but validating that code under realistic, failure-prone conditions is usually slow, inconsistent, and hard to reproduce.

SPOOLER compresses that loop.

Choose a scenario, choose a challenge level, drop in a payload, click **Build It**, and get a deterministic environment package you can run immediately or hand off to someone else.

---

## Why This Exists

### The Team Pain Point This Targets

The underlying workflow problem is not writing code.

The problem is validating behavior under stress conditions that often break real systems:

- high latency
- packet loss
- tight resource budgets
- dependency outages
- auth edge cases
- vulnerable feature flags and security toggles

In fast-moving teams, this usually becomes ad hoc testing.

Ad hoc testing means:

- inconsistent reproduction
- weak confidence in fixes
- slow triage after regressions

SPOOLER turns that into an explicit, reusable package.

## What SPOOLER Produces

Every build generates:

- `recipes/spool-<timestamp>.yml`
- `injections/spool-<timestamp>/payload.<ext>`
- `injections/spool-<timestamp>/bootstrap.sh`

These files are sufficient to recreate the same scenario consistently.

---

## Product Surface

### Simple Mode (Primary Fast Path)

Simple Mode is intentionally reduced to a small number of controls:

- preset scenario
- challenge level
- injection zone (drag-and-drop, browse, or paste)

Then click **Build It**.

### Why Simple Mode Matters

Simple Mode is optimized for speed during rapid validation and early verification.

It allows non-experts to generate meaningful environment recipes without touching 12 low-level controls.

### Advanced Mode (Full Control)

Advanced Mode exposes all environment controls and optional local spin-up:

- intent text
- injection language
- network profile
- latency
- packet loss
- CPU budget
- memory budget
- database engine
- six fault/security toggles
- target path inside container
- optional run command
- optional local `docker compose up -d`

---

## How It Works End to End

### Step 1: Define Scenario

A scenario is set by preset + challenge profile, with optional advanced overrides.

### Step 2: Provide Payload

You can:

- drag and drop a code file
- browse for a code file
- paste code directly

Supported upload extensions:

- `.py`
- `.js`
- `.ts`
- `.tsx`
- `.sh`
- `.bash`
- `.zsh`
- `.txt`
- `.json`
- `.md`

File upload automatically infers language when possible and updates default target path/run command.

### Step 3: Build Package

On **Build It**, SPOOLER writes:

- compose recipe in `recipes/`
- payload and bootstrap in `injections/<run-id>/`

### Step 4: Runtime Injection Model

At container start:

1. `injections/<run-id>` is mounted to `/opt/spooler/injection`.
2. `bootstrap.sh` copies `payload.<ext>` to `SPOOLER_TARGET_PATH`.
3. If `SPOOLER_RUN_COMMAND` is non-empty, it executes.

### Step 5: Optional Local Spin-Up

If enabled in Advanced Mode, SPOOLER attempts:

`docker compose -f recipes/spool-<timestamp>.yml up -d --remove-orphans`

---

## The Mock File Question (What It Is Actually For)

This is the key mental model:

The sample file is not your full application.

It is a **probe payload** that gets injected into the target container path and optionally executed.

Use it to:

- verify environment variables are being passed correctly
- simulate retry/backoff behavior under stress
- demonstrate deterministic reproduction of failure modes
- show how generated code or test code behaves in hostile presets

In short:

The payload is your controllable test probe.

---

## Validation Payload Pack

Use these files as ready-to-run payload options:

- `payload_probes/xbow_qa_probe.py`
- `payload_probes/xbow_qa_probe.js`
- `payload_probes/xbow_qa_probe.sh`

How to use it:

1. In SPOOLER, choose a preset (for example `CPU Spike Recovery` or `Packet Loss Retry Trap`).
2. Drag/drop a payload file into Injection Zone.
3. Keep matching target path/run command for the selected language.
4. Click **Build It**.
5. Optionally run the generated compose command.

What it validates:

- reads environment variables from generated recipe
- simulates dependency instability
- applies retries with exponential backoff
- exits non-zero when retries are exhausted

---

## Operator Docs Included

- `docs/OPERATIONS_RUNBOOK.md` for a concise live walkthrough flow and fallback handling
- `docs/PORTFOLIO_PITCH.md` for portfolio text and executive talking points

---

## Scenario Catalog (Current Presets)

- Slow Mobile + Vulnerable DOM
- Auth Chaos Drill
- SQL Storm + Tight Limits
- Third-Party Timeout Cascade
- CPU Spike Recovery
- Memory Pressure Leak Hunt
- Packet Loss Retry Trap
- Offline-First Failover
- No-DB Fallback Path
- Full Chaos Fire Drill

Challenge levels:

- Preset Default
- Mild
- Balanced
- Hard
- Extreme

---

## Environment Variable Contract

SPOOLER writes these variables into `spool-target`:

- `INTENT`
- `NETWORK_PROFILE`
- `LATENCY_MS`
- `PACKET_LOSS_PCT`
- `CPU_BUDGET`
- `MEMORY_BUDGET`
- `DB_ENGINE`
- `SPOOLER_TARGET_PATH`
- `SPOOLER_RUN_COMMAND`
- `CHAOS_MODE`
- `VULNERABLE_DOM`
- `SQL_INJECTION`
- `AUTH_BYPASS`
- `THIRD_PARTY_OUTAGE`
- `STRICT_RATE_LIMIT`

DB sidecar behavior:

- `Postgres 15` -> adds `postgres:15` service
- `MySQL 8` -> adds `mysql:8` service
- `MongoDB 7` -> adds `mongo:7` service
- `SQLite (No DB Container)` -> no DB sidecar service

---

## Quick Start

### 1. Local Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run App

```bash
streamlit run app.py
```

### 3. Build a Recipe

- choose preset
- choose challenge level
- upload or paste payload
- click **Build It**

### 4. Start Generated Environment (Optional)

```bash
docker compose -f recipes/spool-<timestamp>.yml up -d --remove-orphans
```

### 5. Tear Down

```bash
docker compose -f recipes/spool-<timestamp>.yml down -v
```

---

## 60-Second Rapid Walkthrough

1. Open SPOOLER and pick `Packet Loss Retry Trap`.
2. Set challenge to `Hard`.
3. Upload `payload_probes/xbow_qa_probe.py`.
4. Click **Build It**.
5. Show generated files in `recipes/` and `injections/`.
6. Run generated compose command.
7. Explain that the same run can now be replayed by anyone from the emitted artifacts.

---

## Repository Layout

```text
SPOOLER/
  app.py
  requirements.txt
  README.md
  assets/
    Spooler_logo.png
    SPOOLER_background.png
  payload_probes/
    xbow_qa_probe.py
    xbow_qa_probe.js
    xbow_qa_probe.sh
  docs/
    OPERATIONS_RUNBOOK.md
    PORTFOLIO_PITCH.md
  recipes/
    spool-<timestamp>.yml
  injections/
    spool-<timestamp>/
      payload.<ext>
      bootstrap.sh
```

---

## Current Constraints

- `spooler/target-agent:latest` is assumed to exist locally or in accessible registry.
- IDE Connect is currently a concept-only UI section (not wired to real IDE APIs yet).
- Local spin-up uses Docker CLI availability on host machine.
- Network stress is represented via environment configuration in recipe output (not full Linux traffic shaping in current build).

---

## Suggested Next Iteration (Portfolio Roadmap)

### 1. Monorepo Expansion

Split into clear modules:

- `ui/` Streamlit front end
- `orchestrator/` recipe generation and validation
- `injector/` bootstrap generation and payload contract
- `profiles/` scenario presets and difficulty models
- `runner/` local and CI execution adapters

### 2. CI Validation Matrix

Generate matrix builds for presets + difficulty combinations with pass/fail reports.

### 3. Real IDE Connector

Replace concept expander with actual read-only file import from selected IDE workspace.

### 4. Artifact Registry

Store generated scenario packages with metadata for replay and audit.

---

## Portfolio Talking Points

- Demonstrates product thinking, not just scripting.
- Balances fast UX (Simple Mode) with depth (Advanced Mode).
- Produces deterministic artifacts for reproducibility.
- Turns vague "test it in bad environments" into a concrete, replayable workflow.
- Designed as a base for scaling into a broader environment-testing monorepo.

---

## License

No license file is currently included in this repository.
Add one before publishing if you want clear reuse terms.
