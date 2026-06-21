# Arlo Audit Transparency: Phased Implementation Plan

_Written 2026-06-20. Builds on `docs/transparency-report.md` and deep codebase research._

---

## Overview

A verifiable comparison audit requires that independent observers can, using only publicly-published artifacts, replicate every mechanically-determined step: sample draw, risk measurement, and discrepancy detection. Today all the math is in Arlo and all the data can be exported, but there is no workflow that ties it together, no scripts that demonstrate replication, and no machine-readable output format that makes replication easy.

This plan has two tracks:

**Track A — Observer Toolkit** (implement first, no Arlo changes required):
Tests and scripts that walk through a complete 2-round ballot comparison audit, export artifacts phase by phase, and independently verify every calculation.

**Track B — Arlo Improvements** (implement after Track A proves what's needed):
Changes to Arlo's API and UI that make the Track A workflow easy for officials and observers to follow in production.

---

## Glossary

| Term | Meaning |
|------|---------|
| AA | Audit Admin (state-level) |
| JA | Jurisdiction Admin (county-level) |
| AB | Audit Board |
| CVR | Cast Vote Record — machine record of every ballot |
| Imprinted ID | Tabulator/Batch/Position identifier stamped on ballot |
| Ticket number | Fractional decimal from `consistent_sampler` — determines selection |
| Diluted margin | `margin_votes / total_universe_ballots` |
| `counted_as` | Supersimple discrepancy score: −2,−1,0,+1,+2 |
| SHA-256 bundle | ZIP with a companion `*-sha256-hash.txt` inside |

---

## Track A: Observer Toolkit

### A1. Pytest Integration Test Suite

**Goal:** A single pytest run that exercises a complete 2-round ballot comparison audit and, at each phase transition, calls every export endpoint and saves the artifacts to a temp directory with SHA-256 hashes recorded in a JSON manifest. This becomes both a regression test suite and a live demonstration of the audit trail.

**Location:** `server/tests/ballot_comparison/test_transparency_workflow.py`

#### A1.1 Test structure

```
test_transparency_full_2_round_audit
    ├── setup_audit()         → JSON manifest with hashes of inputs
    ├── pre_seed_exports()    → manifest CSVs, CVR CSVs, standardized contests
    ├── seed_and_sample()     → seed recorded, round 1 retrieval lists
    ├── round_1_audit()       → interpretations entered, round 1 finished
    ├── round_1_exports()     → audit report through round 1
    ├── round_2_sample()      → round 2 retrieval lists
    ├── round_2_audit()       → round 2 finished
    └── final_exports()       → final audit report, reproducibility bundle
```

**Each phase helper should:**
1. Call the relevant API endpoints on the test client
2. Write artifacts to `tmp_path/<phase>/` with original filenames
3. Compute `sha256sum` of each file
4. Append an entry to a `phase_manifest.json`:
   ```json
   {
     "phase": "pre_seed",
     "timestamp": "...",
     "artifacts": [
       {"filename": "J1_ballot_manifest.csv", "sha256": "...", "endpoint": "..."},
       ...
     ]
   }
   ```
5. Assert that the artifact content matches expected shape (columns, row count)

**Fixtures to build on:**
- `conftest.py` in `server/tests/ballot_comparison/` already provides `org_id`, `election_id`, `jurisdiction_ids`, `contest_ids`, `election_settings`, `manifests`, `cvrs`, `round_1_id`
- `run_audit_round()` in `server/tests/helpers.py` handles interpretation entry at a given vote ratio
- The `round_2_id` fixture in existing conftest shows the full 2-round sequence

#### A1.2 Phase-by-phase artifact exports

**Phase 0 — Audit creation (no exports; assertions only)**
- Assert election created with `AuditType.BALLOT_COMPARISON`
- Assert settings: risk limit, seed, audit name, state

**Phase 1 — Pre-seed (upload complete, before seed is fixed)**
- `GET /election/<id>/jurisdiction/<jid>/ballot-manifest/csv` → `<jname>_ballot_manifest.csv`
- `GET /election/<id>/jurisdiction/<jid>/cvrs/csv` → `<jname>_cvrs.csv`
- `GET /election/<id>/jurisdiction/<jid>/standardized-contests/csv` (if it exists) → `<jname>_standardized_contests.csv`
- `GET /election/<id>/standardized-contests/file` → `standardized_contests.csv`
- Validate each manifest: columns present, batch counts > 0, ballot counts > 0, no negative numbers
- Validate each CVR: ImprintedId present, BallotType present, one column per contest choice
- Cross-validate manifest vs. CVR: every (Tabulator, Batch, RecordId) in CVR appears in manifest; batch ballot counts match
- Record SHA-256 of each file in phase manifest

**Phase 2 — Post-seed, pre-round-1**
- Record seed from `GET /election/<id>/settings` (the `randomSeed` field)
- `GET /election/<id>/sample-sizes/1` → `sample_sizes_round1.json`
- `POST /election/<id>/round` (starts round 1)
- `GET /election/<id>/jurisdiction/<jid>/round/<rid>/ballots/retrieval-list` → `<jname>_round1_retrieval_list.csv` (for each jurisdiction)
- Validate retrieval list: columns (Tabulator, Batch Name, Ballot Number, Imprinted ID, Ticket Numbers, Status)
- Assert retrieval list count ≤ sample size
- Record SHA-256 of each retrieval list

**Phase 3 — Round 1 audit complete**
- (Simulate audit board entries via `run_audit_round`)
- `POST /election/<id>/round/current/finish`
- `GET /election/<id>/report` → `audit_report_round1.txt`
- `GET /election/<id>/discrepancy-report` → `discrepancy_report_round1.csv`
- Parse the pseudo-CSV audit report: extract ROUNDS section rows, assert p-value and `is_complete` fields
- If audit not complete: proceed to Phase 4

**Phase 4 — Round 2 setup**
- `GET /election/<id>/sample-sizes/2` → `sample_sizes_round2.json`
- `POST /election/<id>/round`
- `GET /election/<id>/jurisdiction/<jid>/round/<rid>/ballots/retrieval-list` → `<jname>_round2_retrieval_list.csv`
- Validate as in Phase 2; assert round 2 list is a superset of round 1 (same ballots plus new ones)
- Record SHA-256

**Phase 5 — Final**
- `GET /election/<id>/report` → `audit_report_final.txt`
- `GET /election/<id>/discrepancy-report` → `discrepancy_report_final.csv`
- Assert at least one targeted contest has risk limit met in final report
- Write `reproducibility_bundle.json` (see A1.3)

#### A1.3 Reproducibility bundle

At the end of Phase 5, the test generates a `reproducibility_bundle.json` that contains everything an independent observer needs to replay the audit from scratch:

```json
{
  "election": {"name": "...", "state": "...", "risk_limit_pct": 10},
  "contests": [
    {
      "name": "Contest 1",
      "targeted": true,
      "choices": {"Alice": 5000, "Bob": 4000},
      "total_ballots_cast": 10000
    }
  ],
  "random_seed": "1234567890",
  "jurisdictions": [
    {
      "name": "J1",
      "manifest_sha256": "...",
      "cvr_sha256": "...",
      "batches": [
        {"tabulator": "TABULATOR1", "name": "BATCH1", "ballot_count": 20}
      ]
    }
  ],
  "rounds": [
    {
      "round_num": 1,
      "sample_sizes": {"Contest 1": 45},
      "retrieval_list_sha256s": {"J1": "...", "J2": "..."},
      "p_values": {"Contest 1": 0.38},
      "complete": false
    },
    {
      "round_num": 2,
      "sample_sizes": {"Contest 1": 90},
      "retrieval_list_sha256s": {"J1": "...", "J2": "..."},
      "p_values": {"Contest 1": 0.04},
      "complete": true
    }
  ]
}
```

---

### A2. Official Export Scripts

**Goal:** Standalone scripts (no Arlo source code required) that an election official runs against a live or test Arlo instance to export and hash artifacts at each phase. Output is a directory tree with artifacts and a signed JSON manifest ready for public posting.

**Location:** `scripts/transparency/`

#### `scripts/transparency/export_phase.py`

```
usage: export_phase.py --url ARLO_URL --election ELECTION_ID \
       --phase {pre_seed,post_seed,post_round,final} \
       --round ROUND_NUM \
       --output-dir OUTPUT_DIR
```

Authentication: reads a session token from `--token` or `ARLO_SESSION_TOKEN` env var (obtained by logging in via browser and copying the cookie).

**Behavior per phase:**

`pre_seed`:
- Downloads manifest CSV, CVR CSV per jurisdiction
- Downloads standardized contests file
- Downloads audit settings (via `GET /election/<id>` JSON response)
- Writes all to `output_dir/pre_seed/`
- Computes SHA-256 of each; writes `pre_seed_manifest.json`

`post_seed`:
- Downloads round N retrieval list per jurisdiction
- Downloads sample sizes JSON
- Writes `post_seed_round_<N>_manifest.json`

`post_round`:
- Downloads audit report
- Downloads discrepancy report
- Writes `post_round_<N>_manifest.json`

`final`:
- Downloads final audit report
- Writes `final_manifest.json`
- Optionally generates `reproducibility_bundle.json`

#### `scripts/transparency/hash_and_sign.py`

```
usage: hash_and_sign.py manifest.json [--sign-with KEY_FILE]
```

Reads a phase manifest JSON, verifies SHA-256 of each listed file, and optionally produces a detached PGP signature of the manifest. Prints a summary table and a publication-ready statement:

```
Pre-seed artifact bundle verified — 2026-10-15T10:32:00Z
Files:
  J1_ballot_manifest.csv      sha256: abc123...
  J1_cvrs.csv                 sha256: def456...
  standardized_contests.csv   sha256: ghi789...

Sign this manifest and publish it to your public repository
BEFORE entering the random seed.
```

---

### A3. Observer Verification Scripts

**Goal:** Scripts that an independent observer runs, given only the publicly-posted artifacts, to replicate every mechanically-determined step.

**Location:** `scripts/transparency/observer/`

All scripts are standalone — they import only `consistent_sampler` (installable via `pip install consistent-sampler`) and standard library. No Arlo server code required.

#### `observer/verify_manifests.py`

```
usage: verify_manifests.py --manifest-dir DIR
```

1. Reads all `*_ballot_manifest.csv` files
2. Validates columns (Tabulator, Batch Name, Number of Ballots)
3. Checks for duplicate (Tabulator, Batch) pairs
4. Sums ballot counts per tabulator, per jurisdiction
5. Reads the CVR file if present: verifies every (Tabulator, Batch, RecordId) in the CVR exists in the manifest with sufficient ballot count
6. Reports discrepancies

#### `observer/replicate_sample.py`

```
usage: replicate_sample.py \
  --seed SEED \
  --manifest-dir DIR \          # directory with jurisdiction manifest CSVs
  --sample-sizes FILE \         # sample_sizes_round<N>.json from official export
  --round ROUND_NUM \
  [--expected-retrieval-list DIR]   # compare against official retrieval lists
```

**Algorithm:**
1. Read all jurisdiction manifests; build the universe list: one entry per (jurisdiction, tabulator, batch, ballot_position) ordered by jurisdiction name, then tabulator, then batch, then ballot position
2. Concatenate all entries into a single ordered list (consistent with how Arlo builds it in `compute_sample_ballots()`)
3. Call `consistent_sampler.sample_by_index(universe, sample_size, seed, with_replacement=False)` for each contest
4. Merge results across contests (union of sampled ballots)
5. Format as a retrieval list: (Jurisdiction, Tabulator, Batch Name, Ballot Number, Imprinted ID — from CVR, Ticket Numbers)
6. If `--expected-retrieval-list` is given, diff against official list line-by-line; report any discrepancies

This is the core independent replication step. A successful match proves that the sample was drawn from the published seed and manifest without manipulation.

**Key implementation detail:** Arlo's `draw_sample` task in `server/api/rounds.py` calls `sampler.draw_sample()` from `server/audit_math/sampler.py`. The universe ordering is deterministic given the manifest. The observer script must replicate this ordering exactly. The code for this is in `server/audit_math/sampler.py` and `server/api/rounds.py` (`compute_sample_ballots`). Document the exact ordering in a comment in the observer script.

#### `observer/replicate_pvalue.py`

```
usage: replicate_pvalue.py \
  --cvr FILE \                        # jurisdiction CVR CSVs (one or more)
  --audit-report FILE \               # official audit report (pseudo-CSV)
  --contest-name "Contest 1" \
  --risk-limit 0.10 \
  --round ROUND_NUM
```

**Algorithm:**
1. Parse the SAMPLED BALLOTS section of the audit report to get:
   - For each sampled ballot: Imprinted ID, CVR result, Audit result, `counted_as` discrepancy
2. Parse the CVR file to build a lookup: Imprinted ID → CVR interpretation per contest
3. For each sampled ballot: verify that the `CVR Result` column in the report matches what the CVR file says for that Imprinted ID; flag mismatches
4. Build `sampled_cvrs` dict: Imprinted ID → `{contest: {choice: count, "sampled": 1}}`
5. Build `cvrs` dict (all CVR ballots): same structure
6. Call `server.audit_math.supersimple.compute_risk(risk_limit, contest, cvrs, sampled_cvrs)` → `(p_value, is_complete)`
7. Compare computed p-value against the value in the ROUNDS section of the audit report
8. Also call `supersimple.compute_discrepancies()` and compare `counted_as` values against the SAMPLED BALLOTS section

**Note:** This script imports from `server.audit_math` — it requires a copy of the Arlo source. A fully standalone version would re-implement `supersimple.py`'s `nMin` and `compute_risk()` in ~50 lines, which is a good future step.

#### `observer/end_to_end_verify.py`

```
usage: end_to_end_verify.py --artifact-dir DIR --round ROUND_NUM
```

Orchestrates the above scripts in sequence and prints a verification report:

```
=== Arlo Audit Independent Verification Report ===
Election: General Election 2026
Contest: Governor
Round: 1

[PASS] SHA-256 hashes match published manifest
[PASS] Ballot manifests valid (3 jurisdictions, 12 batches, 6240 ballots)
[PASS] CVR consistent with manifest (6240 ballots, all batches present)
[PASS] Sample draw replicated (45 ballots match official retrieval list)
[PASS] CVR results in audit report match CVR file
[PASS] Discrepancy scores match (0 type-2, 1 type-1, 44 type-0)
[PASS] P-value replicated: computed=0.38, reported=0.38
      Risk limit (10%) NOT MET — round 2 required.

=== Summary ===
All checks passed. The reported p-value is independently reproducible.
```

---

### A4. Test Coverage for Observer Scripts

**Location:** `server/tests/transparency/`

Three test files:

`test_replicate_sample.py`:
- Use the same fixtures as `test_ballot_comparison.py`
- After `round_1_id` fixture, call the API to get retrieval list
- Run `replicate_sample.py` main function with seed + manifest
- Assert output matches retrieved list exactly

`test_replicate_pvalue.py`:
- After `round_1_id` fixture finishes and round is completed
- Export audit report via API
- Run `replicate_pvalue.py` with that report + CVR
- Assert computed p-value matches `round_contest.end_p_value` in DB

`test_end_to_end_verify.py`:
- Drives a full 2-round audit using fixtures
- Exports all phase artifacts to `tmp_path`
- Writes phase manifests
- Runs `end_to_end_verify.py` for round 1 and round 2
- Asserts all checks `[PASS]`

---

## Track B: Arlo Improvements

Ordered by priority. Each item names the server files to change and the API surface added.

---

### B1. Machine-Readable Audit Report (High Priority)

**Problem:** `GET /election/<id>/report` returns pseudo-CSV with `######## SECTION ########` headers. It is not parseable by standard CSV tools. There is no JSON or HTML alternative.

**Change:** Add `GET /election/<id>/report.json` (or add `Accept: application/json` content negotiation to the existing endpoint).

**Response shape:**
```json
{
  "election": {...},
  "contests": [...],
  "settings": {...},
  "rounds": [
    {
      "round_num": 1,
      "contests": [
        {
          "name": "Contest 1",
          "targeted": true,
          "sample_size": 45,
          "p_value": 0.38,
          "risk_limit_met": false,
          "audited_votes": {"Alice": 22, "Bob": 21, "Undervote": 2}
        }
      ],
      "started_at": "...",
      "ended_at": "..."
    }
  ],
  "sampled_ballots": [
    {
      "jurisdiction": "J1",
      "tabulator": "TABULATOR1",
      "batch_name": "BATCH1",
      "ballot_position": 3,
      "imprinted_id": "1-1-3",
      "ticket_numbers": {"Contest 1": "0.234..."},
      "audited": true,
      "cvr_result": {"Contest 1": {"Alice": 1, "Bob": 0}},
      "audit_result": {"Contest 1": {"Alice": 1, "Bob": 0}},
      "discrepancy": {"Contest 1": 0}
    }
  ]
}
```

**Files:** `server/api/reports.py` — add a new route or branch on `request.accept_mimetypes`. The data assembly is already done in `election_report()` and `sampled_ballots_rows()`.

**Test:** `server/tests/api/test_reports.py` — add JSON report assertions alongside existing snapshot tests.

---

### B2. Opportunistic Contest Risk Levels (High Priority)

**Problem:** Opportunistic contests receive no p-value at all. A contest with zero sampled ballots has a formal risk of 100%, but this is not reported anywhere — neither in the API response nor in the audit report.

**Change 1:** In `calculate_risk_measurements()` (`server/api/rounds.py`), for opportunistic contests compute and store `end_p_value` even if it is 1.0 (or the value from the supersimple formula with zero sampled ballots).

**Change 2:** Add a `universe_ballot_count` field per contest to the sample sizes response (`server/api/sample_sizes.py`) — the count of ballots in the sampling universe for that contest. This is the denominator for the diluted margin.

**Change 3:** In the audit report (both CSV and new JSON), include opportunistic contest p-values with a note: `"Risk limit not met — no ballots sampled for this contest (formal risk: 100%)"` for zero-sample contests.

**Files:** `server/api/rounds.py` (`calculate_risk_measurements`), `server/api/sample_sizes.py`, `server/api/reports.py`.

---

### B3. Sampler Inputs Artifact (Medium Priority)

**Problem:** An observer wanting to replicate the sample draw must reconstruct the sampling universe from the individual manifest CSVs. There is no single "sampler inputs" artifact that packages everything needed.

**Change:** Add `GET /election/<id>/round/<id>/sampler-inputs` — returns a JSON artifact that contains everything needed to replicate the sample draw without downloading individual manifest CSVs:

```json
{
  "random_seed": "1234567890",
  "round_num": 1,
  "contests": [
    {"name": "Contest 1", "sample_size": 45, "universe_ballot_count": 6240}
  ],
  "jurisdictions": [
    {
      "name": "J1",
      "batches": [
        {"tabulator": "TABULATOR1", "name": "BATCH1", "ballot_count": 20},
        ...
      ]
    }
  ]
}
```

This artifact, together with the CVR files and audit report, is sufficient to independently replicate everything.

**Files:** New route in `server/api/rounds.py` or a new `server/api/sampler_inputs.py`.

---

### B4. Pre-seed Hash-Index JSON Endpoint (Medium Priority)

**Problem:** The canonical pre-seed transparency artifact should be a JSON file containing hashes of all uploaded input files. Currently officials must download each file separately and hash them manually. The batch comparison SHA-256 bundle endpoints show the pattern.

**Change:** Add `GET /election/<id>/pre-seed-bundle` — assembles and hashes all uploaded input files (manifests, CVRs, standardized contests) and returns:

```json
{
  "generated_at": "2026-10-15T10:32:00Z",
  "election_id": "...",
  "election_name": "General Election 2026",
  "state": "WA",
  "risk_limit_pct": 10,
  "jurisdictions": [
    {
      "name": "J1",
      "ballot_manifest": {"filename": "manifest.csv", "sha256": "...", "ballot_count": 120},
      "cvr": {"filename": "cvrs.csv", "sha256": "...", "ballot_count": 120}
    }
  ],
  "standardized_contests": {"filename": "standardized_contests.csv", "sha256": "..."},
  "contests": [
    {"name": "Contest 1", "choices": {"Alice": 5000, "Bob": 4000}, "total_ballots_cast": 10000}
  ]
}
```

Officials download this JSON, sign it with PGP or a digital certificate, and publish it before entering the seed. The SHA-256 values let observers verify they have the right files.

**Files:** New `server/api/pre_seed_bundle.py`.

---

### B5. Per-Jurisdiction Phase Exports of New Data Only (High Priority)

**Problem:** Each county-level JA only needs to export the *new* data for the current phase. There is no per-jurisdiction bundle per phase. CVRs and manifests are not re-bundled unnecessarily.

**Change:** Add three per-jurisdiction bundle endpoints:
- `GET /election/<id>/jurisdiction/<id>/phase-export/pre-seed` → ZIP of manifest + CVR + SHA-256 hashes JSON
- `GET /election/<id>/jurisdiction/<id>/phase-export/post-seed?round=1` → ZIP of retrieval list + SHA-256 hashes
- `GET /election/<id>/jurisdiction/<id>/phase-export/post-audit?round=1` → ZIP of jurisdiction audit report + SHA-256 hashes

Each ZIP includes a `manifest.json` with filename and hash of each file.

**Files:** New `server/api/jurisdiction_phase_exports.py`.

---

### B6. UI Guidance for Transparency Workflow (High Priority)

**Problem:** Arlo provides no guidance to officials about when to export, hash, publish, and timestamp artifacts. The current UI flows directly from upload to seed entry with no transparency checkpoint.

**Change:** Add a "Transparency Checklist" panel to the audit admin dashboard that appears at each phase transition:

- **After all manifests and CVRs uploaded, before seed entry:**
  > Before entering the random seed, download and publish the pre-seed bundle. Have your official sign the JSON manifest and post it publicly with a timestamp. [Download pre-seed bundle] [Mark as published]

- **After seed entered, before round start:**
  > Before retrieving ballots, publish the retrieval lists so observers can verify the sample. [Download round 1 retrieval lists] [Mark as published]

- **After round complete:**
  > Publish the updated audit report before starting the next round. [Download audit report] [Mark as published]

The "Mark as published" button records a `published_at` timestamp in the DB (new column on `Election` or a new `PublicationRecord` table). This is a soft gate — it does not block the audit from proceeding — but makes the best-practice workflow explicit and auditable.

**Files:** React components in `client/src/`, new DB migration in `server/migrations/`, new columns or table in `server/models.py`.

---

### B7. Reproducibility Bundle (Medium Priority)

**Problem:** There is no single artifact that, together with the published CSVs, lets an observer replay the entire audit.

**Change:** Add `GET /election/<id>/reproducibility-bundle` after the audit is complete. Returns a ZIP containing:
- `reproducibility_bundle.json` (see A1.3 above)
- `README.md` with instructions for running `observer/end_to_end_verify.py`
- A copy of `scripts/transparency/observer/` (the verification scripts themselves)

This makes the reproducibility bundle self-contained: an observer downloads one ZIP and can verify everything.

**Files:** New `server/api/reproducibility_bundle.py`.

---

### B8. RFC 3161 Timestamping Support (Lower Priority)

**Problem:** "Published at" timestamps are self-asserted. RFC 3161 trusted timestamps from a free TSA (e.g., freetsa.org) provide cryptographic proof of publication time, binding the artifact hash to a trusted time source.

**Change:** Add a `timestamp_artifact(file_bytes, filename)` utility in `server/util/timestamp.py` that:
1. Computes SHA-256 of the bytes
2. Posts to a configured RFC 3161 TSA (`ARLO_TSA_URL`)
3. Returns the DER-encoded timestamp token
4. Stores it alongside the artifact (locally or in S3)

Wire this into `generate_pre_seed_bundle()` and `generate_reproducibility_bundle()`.

**Files:** `server/util/timestamp.py`, updated bundle endpoints.

---

## Implementation Sequence

```
Week 1-2:  A1 — Pytest transparency test suite (2-round, phase-by-phase)
Week 3:    A2 — Official export scripts (export_phase.py, hash_and_sign.py)
Week 4:    A3 — Observer verification scripts (replicate_sample.py, replicate_pvalue.py)
Week 5:    A4 — Tests for observer scripts
Week 6:    B1 — JSON audit report endpoint
Week 7:    B2 — Opportunistic contest risk levels + universe ballot count
Week 8:    B3 — Sampler inputs artifact
Week 9:    B4 — Pre-seed hash-index JSON endpoint
Week 10:   B5 — Per-jurisdiction phase exports
Week 11+:  B6 — UI transparency checklist (multi-week, involves React)
           B7 — Reproducibility bundle
           B8 — RFC 3161 timestamping
```

---

## Key Code Locations

| Topic | File | Notes |
|-------|------|-------|
| Sample drawing | `server/api/rounds.py` `draw_sample()` | Background task; calls `compute_sample_ballots()` |
| Sampler math | `server/audit_math/sampler.py` | Wraps `consistent_sampler` |
| P-value computation | `server/audit_math/supersimple.py` | `compute_risk()`, `compute_discrepancies()` |
| Discrepancy scores | `server/audit_math/supersimple.py` `compute_discrepancies()` | Returns `counted_as` per ballot |
| Audit report | `server/api/reports.py` | `election_report()`, `sampled_ballots_rows()` |
| Sample sizes | `server/api/sample_sizes.py` | Returns options for each round |
| CVR parsing | `server/api/cvrs.py` | Handles Dominion, ESS, ClearBallot, Hart |
| Retrieval list | `server/api/ballots.py` `ballot_retrieval_list()` | Columns: Tabulator, Batch, Ballot Number, Imprinted ID, Ticket Numbers, Status |
| Existing 2-round test | `server/tests/ballot_comparison/test_ballot_comparison.py` | Template for A1 |
| Test helpers | `server/tests/helpers.py` | `run_audit_round()`, `set_logged_in_user()` |
| Test fixtures | `server/tests/ballot_comparison/conftest.py` | `round_1_id`, `round_2_id`, etc. |
| nOAuth | `server/nOAuth/app.py` | Pass-through OAuth; used in dev/test |
| File storage | `server/util/file.py` | `retrieve_file()`, local vs. S3 |
| Background tasks | `server/worker/worker.py` | 2-sec polling loop |

---

## Open Questions

1. **CVR redaction:** Arlo does not redact rare-style ballots before export. For production, the pre-seed export script should warn if a jurisdiction's CVR has ballot styles appearing only once (potential vote revelation risk). Should Arlo compute and display a "redaction risk score" per CVR? Or just document the responsibility?

2. **Universe ordering:** The exact ordering of ballots in `compute_sample_ballots()` determines the sample. The observer script must replicate this precisely. Is the ordering stable and documented? (Currently it is deterministic but not explicitly specified.) Should it be formally documented as part of the audit protocol?

3. **Opportunistic contest risk threshold:** When there are zero sampled ballots for an opportunistic contest, reporting 100% risk is technically correct but may be alarming. Should the UI explain this differently (e.g., "Not sampled — risk not calculated") or always use the mathematically correct 100%?

4. **Auth for observer scripts:** The observer scripts need an Arlo session token. For testing, `FLASK_ENV=development` nOAuth accepts any email. For production, should Arlo add a read-only "observer" role with a long-lived API token for downloading public artifacts, rather than requiring a full audit-admin login?
