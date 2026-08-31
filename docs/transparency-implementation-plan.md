# Arlo Audit Transparency: Phased Implementation Plan

_Written 2026-06-20. Builds on `docs/transparency-report.md` and deep codebase research._

---

## Overview

### The software-independence problem

The purpose of a risk-limiting audit is *software independence*: the ability to detect errors in the voting system — including its CVRs — without relying on the same software stack that produced them. Audit support software like Arlo helps us accomplish that, but it needs independent observers and verification. They check that the evidence is sufficient to support the audit conclusions. Do the manifests and CVRs match the reported results? Did the interpretations of the human audit boards and independent risk calculations match the Arlo reports?

It is important to have **human observers who are physically present during audit board sessions**, maintaining their own silent, independent record of ballot interpretations. Their record is then compared — after the session, not during — against the Arlo audit report. This comparison and verification chain should remain independent of every computer system and individual responsible for the initial reported results.

**The blind-audit principle** is what makes this work: audit boards must interpret each ballot without seeing the voting system's interpretation. If anyone communicates the voting system's interpretation to the board — observers, officials, Arlo, or a screen visible in the room — the board's interpretations could be tainted. Observers must be silent: recording what they hear, never reacting, never speaking to boards, never revealing whether a ballot looks like a discrepancy.

### Two classes of verification

| Verification class | Who does it | When | Tools needed |
|--------------------|------------|------|-------------|
| **Mechanical** (sample draw, risk level) | Any observer with a computer | After artifacts are published | `replicate_sample.py`, `replicate_risk_level.py` |
| **Human** (board vs. paper vs. CVR vs. Arlo record) | Observers physically present during audit | During each board session | Redacted CVR and selection list, pen |

Both classes are necessary. Neither is sufficient alone.

### How the human observer layer actually works

Observers cannot write fast enough to transcribe what they hear, and they must not interfere with the board. What they can do is **follow along via an excerpt of selected ballots from the CVR** and mark any discrepancy.

The excerpt is produced by joining the retrieval list with the CVR: for each sampled ballot in physical retrieval order, it shows the ballot's imprinted ID and the voting system's recorded interpretation of each contest on that ballot. The observer holds this printout, listens as the board calls out each contest aloud (typically twice for double-checking), and notes any vote where what they hear differs from what is printed.The format is right-justified by contest name so the eye can scan down a column of values quickly.

The audit board **never sees the CVR** — in proper blind practice they have no access to it during the session. They examine only the physical paper ballot. The observer's excerpt must likewise never be shown to the board; it would compromise the independence of the audit by revealing what the CVR says before the board states their own interpretation.

The observer's marked printout is then compared against the Arlo audit report's SAMPLED BALLOTS section. Discrepancies can be checked in two directions:
1. **Observer marked ≠ excerpt printed** → the board saw something different from the CVR (a discrepancy that should appear in Arlo's discrepancy report)
2. **Observer's hearing ≠ Arlo's recorded audit result** → either the board misspoke, the observer mis-heard, or Arlo recorded something other than what the board said

This final comparison can be done entirely on paper — no computer needed — which is what gives it independence from every system the jurisdiction controls.

### CVR anonymization

Before any CVR is published, rare ballot styles (e.g. those with fewer than ~10 ballots in the jurisdiction) must be aggregated to prevent vote revelation — a voter with a unique combination of contest choices could be identified from their CVR row. See [Privacy violations in election results | Science Advances](https://www.science.org/doi/10.1126/sciadv.adt1512), along with
[loriinboulder/anonymize_cvr](https://github.com/loriinboulder/anonymize_cvr), which implements Colorado's requirement (C.R.S. 24-72-205.5) and the approach documented in [Branscomb et al., 2018](http://www.sos.state.co.us/pubs/rule_making/hearings/2018/20180309BranscombEtAl.pdf) (endorsed by McBurnett, Stark, Rivest et al.). Arlo does not currently apply this redaction; it is the jurisdiction's responsibility before publishing the CVR.

### This plan has two tracks

**Track A — Observer Toolkit** (implement first, no Arlo changes required):
Tests and scripts covering both verification classes: mechanical replication of every calculation, and paper-based tools for human observers to independently record and compare audit board interpretations.

**Track B — Arlo Improvements**:
Changes to Arlo's API and UI that make the Track A workflow easy for officials and observers to follow in production.

---

## Glossary

| Term | Meaning |
|------|---------|
| AA | Audit Admin (state-level) |
| JA | Jurisdiction Admin (county-level) |
| AB | Audit Board — the team (typically 2 people) that physically examines ballots and records interpretations |
| CVR | Cast Vote Record — machine record of every ballot |
| Imprinted ID | Tabulator/Batch/Position identifier stamped on ballot |
| Ticket number | Fractional decimal from `consistent_sampler` — determines selection |
| Diluted margin | `margin_votes / total_universe_ballots` |
| `counted_as` | Supersimple discrepancy score: −2,−1,0,+1,+2 |
| SHA-256 bundle | ZIP with a companion `*-sha256-hash.txt` inside |
| CVR Excerpt | Excerpt of the selected ballots from the CVR used by observers to take notes during an auditing session |
| Blind audit | Audit boards never see the CVR at all — they interpret the paper ballot in isolation, and their interpretation is compared to the CVR by both Arlo and the observers . This independence is crucial |
| Rare style | A ballot style (combination of contest choices) appearing in fewer than ~10 ballots — must be aggregated in the public CVR to prevent vote revelation |
| Observer excerpt | Pre-generated printout joining retrieval list with CVR; observer follows along during the board session and marks discrepancys |

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
- Parse the pseudo-CSV audit report: extract ROUNDS section rows, assert risk level and `is_complete` fields
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

### A2. Official Export Functions

**Goal:** Arlo scripts (standalone for now, eventually standard functions) to export and hash artifacts at each phase. Output is a directory tree with artifacts and a signed JSON manifest ready for public posting. Public posting is how observers access the data — they have no Arlo instance access — so publishing each phase bundle to a stable public URL (e.g., a state elections website) is a required step in the workflow, not optional.

**Location:** `scripts/transparency/`

#### `scripts/transparency/export_phase.py`

```
usage: export_phase.py --url ARLO_URL --election ELECTION_ID \
       --phase {pre_seed,post_seed,post_round,final} \
       --round ROUND_NUM \
       --output-dir OUTPUT_DIR
```

Authentication: reads a session token from `ARLO_SESSION_TOKEN` env var (obtained by logging in via browser and copying the cookie).

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

All scripts are standalone.  Arlo server library code reuse is fine.

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

#### `observer/replicate_risk_level.py`

```
usage: replicate_risk_level.py \
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
7. Compare computed risk level against the value in the ROUNDS section of the audit report
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
[PASS] risk level replicated: computed=0.38, reported=0.38
      Risk limit (10%) NOT MET — round 2 required.

=== Summary ===
All checks passed. The reported risk level is independently reproducible.
```

---

### A5. Observer Excerpt Generator

**Goal:** A script that joins the retrieval list with the CVR to produce a print-ready per-ballot excerpt that observers bring into the audit room. The observer follows along as the board reads each contest aloud and documents any vote they hear that differs from what is printed.

**Location:** `scripts/transparency/observer/generate_excerpt.py`

#### Format

The format makes following along easy. Each ballot is separated by a header line containing the imprinted ID bracketed by `<><><><><><><><><>` decorations. Contest names are right-justified in a fixed-width column; the CVR interpretation is printed immediately to the right.

```
<><><><><><><><><><><><><><><><><>><><><><><><>  104-19-48  <><><><><><><><><>
                           Presidential Electors _ Kamala D. Harris / Tim Walz
  Representative to the US Congress - District 7 _ Brittany Pettersen
                                     Amendment G _ Yes/For
                                     Amendment H _ Yes/For
                                     Amendment K _ NO VOTE
                                 Proposition 127 _ No/Against

<><><><><><><><><><><><><><><><><><><><><><><>   105-55-20  <><><><><><><><><>
                           Presidential Electors _ Donald J. Trump / JD Vance
  Representative to the US Congress - District 7 _ Sergei Matveyuk
                               District Attorney _ NO VOTE
                                     Amendment G _ No/Against
```

Ballots appear in physical retrieval order (by tabulator, batch, ballot position within batch) to match the sequence in which the board will handle them. Each ballot shows all contests on its ballot style — not just the targeted audit contests — because the board reads every race. Undervotes appear as `NO VOTE`, not as a blank, to make them explicit and audible.

The observer writes directly on this printout when they hear something different from what is printed. In a zero-discrepancy audit, nothing gets marked.

#### Usage

```
generate_excerpt.py \
  --retrieval-list J1_round1_retrieval_list.csv \
  --cvr J1_cvrs.csv \
  --cvr-format dominion \
  [--output excerpt_J1_round1.txt]
```

- `--retrieval-list`: The retrieval list CSV downloaded from Arlo (columns: Tabulator, Batch Name, Ballot Number, Imprinted ID, Ticket Numbers, Status)
- `--cvr`: The publicly-posted (anonymized) CVR file for this jurisdiction (Dominion, ESS, ClearBallot, or Hart format) — must be the version published before the seed, not a raw Arlo export
- `--cvr-format`: CVR vendor format (determines column parsing)
- `--output`: Output text file; if omitted, prints to stdout for piping to a printer

#### Algorithm

1. Parse the publicly-posted (anonymized) CVR file to build a lookup: `imprinted_id → {contest_name → interpretation}`. For Dominion format:
   - Header row contains contest columns like `"Contest Name (Choice Name)"` after the first 8 fixed columns
   - For each ballot row, collect all (contest, choice) columns where the value is `1`
   - Group by contest name; if no choice has value `1`, record `NO VOTE` for that contest
   - The `BallotType` column determines which contests appear on this ballot style (not all contests appear on all ballot types)
2. Parse the retrieval list to get sampled ballots in order (sort by Tabulator, Batch Name, Ballot Number)
3. For each sampled ballot, look up its imprinted ID in the CVR lookup
4. Compute the display width: the longest contest name across all sampled ballots' styles
5. For each ballot, output the `<><>` header, then each contest name right-padded to the display width, followed by an underscore "_" followed by the interpretation
6. Warn (but do not skip) if an imprinted ID from the retrieval list is not found in the CVR — this may indicate the ballot was in a rare style redacted from the public CVR (see Q1); the jurisdiction must provide the CVR row for that ballot separately, and the gap is itself a finding to report

#### Blind-audit note in the script header

The generated excerpt includes a printed notice at the top:

```
OBSERVER EXCERPT — [Election Name] — [Jurisdiction] — Round [N]
Generated: [timestamp]  SHA-256: [hash of this file]

IMPORTANT: This document shows what the voting system recorded for each ballot.
- DO NOT show this document to the audit board.
- DO NOT communicate with the audit board during the session.
- Audit boards must form their own interpretation of each ballot WITHOUT
  seeing or hearing the CVR. This improves audit integrity.
- Follow along silently. Note any vote where you hear something different
  from what is printed.
- After the session, compare your marked discrepancies against the Arlo
  audit report (SAMPLED BALLOTS section).
```

The SHA-256 hash of the excerpt file is printed so observers can confirm they have the same file as other observers and that it was generated from the published CVR.

#### After the session: paper-based comparison

No additional script is needed for the comparison step. An observer with a marked excerpt does the following on paper:

1. Review the SAMPLED BALLOTS section of the Arlo audit report
2. For each ballot where you marked a discrepancy: find that ballot's row in the report
3. Check the "Audit Result" column — does it match what you heard the board say?
4. Check the "CVR Result" column — does it match what is printed on your excerpt?
5. Check the "Change in Margin" column — does the discrepancy score match the discrepancy you marked?

Discrepancies between the observer's marks and the Arlo report are reported to the audit supervisor, not acted on unilaterally by the observer.

#### Test coverage

`server/tests/transparency/test_generate_excerpt.py`:
- Use the existing `TEST_CVRS` fixture (Dominion format) and a synthetic retrieval list
- Assert that every imprinted ID in the retrieval list appears in the output
- Assert that contests are right-justified to the correct width
- Assert that NO VOTE appears for undervotes
- Assert that the excerpt is in retrieval order (not CVR row order)
- Assert that the SHA-256 printed at the top matches `hashlib.sha256(output.encode()).hexdigest()`

---

### A4. Test Coverage for Observer Scripts

**Location:** `server/tests/transparency/`

Three test files:

`test_replicate_sample.py`:
- Use the same fixtures as `test_ballot_comparison.py`
- After `round_1_id` fixture, call the API to get retrieval list
- Run `replicate_sample.py` main function with seed + manifest
- Assert output matches retrieved list exactly

`test_replicate_risk_level.py`:
- After `round_1_id` fixture finishes and round is completed
- Export audit report via API
- Run `replicate_risk_level.py` with that report + CVR
- Assert computed risk level matches `round_contest.end_p_value` in DB

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

Note this may be worth implementing before some of Track A is implemented.

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

**Problem:** Evidence is generated for opportunistic contests, but risk reduction is not quantified.

**Change 1:** In `calculate_risk_measurements()` (`server/api/rounds.py`), for opportunistic contests compute and store `end_p_value` even if it is 1.0 (or the value from the supersimple formula with zero sampled ballots).

**Change 2:** Add a `universe_ballot_count` field per contest to the sample sizes response (`server/api/sample_sizes.py`) — the count of ballots in the sampling universe for that contest. This is the denominator for the diluted margin.

**Change 3:** In the audit report (both CSV and new JSON), include opportunistic contest risk levels.

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

### B8. Timestamping Support (Lower Priority)

**Problem:** It is crucial that the data to be audited be committed to before the dice roll, so independent timestamps that can be publicly trusted and verified are important. Exact approach TBD.

**Change:** Add a `timestamp_artifact(file_bytes, filename)` utility in `server/util/timestamp.py` that:
1. Computes SHA-256 of the bytes
2. Posts to a suitable, reliable trusted timestamp source (`ARLO_TIMESTAMP_SERVICE`)
3. Returns the timestamp evidence
4. Stores it alongside the artifact

Wire this into `generate_pre_seed_bundle()` and `generate_reproducibility_bundle()`.

**Files:** `server/util/timestamp.py`, updated bundle endpoints.

---

## Implementation Sequence

```
Week 1-2:  A1 — Pytest transparency test suite (2-round, phase-by-phase)
Week 3:    A2 — Official export scripts (export_phase.py, hash_and_sign.py)
Week 4:    A3 — Observer mechanical verification (replicate_sample.py, replicate_risk_level.py)
           A5 — Observer excerpt generator (generate_excerpt.py)
Week 5:    A4 — Tests for A3 and A5 scripts
Week 6:    B1 — JSON audit report endpoint
Week 7:    B2 — Opportunistic contest risk levels + universe ballot count
Week 8:    B3 — Sampler inputs artifact
Week 9:    B4 — Pre-seed hash-index JSON endpoint
Week 10:   B5 — Per-jurisdiction phase exports
Week 11+:  B6 — UI transparency checklist (multi-week, involves React)
           B8 — Timestamping
```

---

## Key Code Locations

| Topic | File | Notes |
|-------|------|-------|
| Sample drawing | `server/api/rounds.py` `draw_sample()` | Background task; calls `compute_sample_ballots()` |
| Sampler math | `server/audit_math/sampler.py` | Wraps `consistent_sampler` |
| risk level computation | `server/audit_math/supersimple.py` | `compute_risk()`, `compute_discrepancies()` |
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

1. **CVR redaction:** The timing and handling of redaction needs more attention. Ideally Arlo would do all necessary redaction up-front. Until then, jurisdictions need to do the redaction on their own. Jurisdictions also need to address what to do when a selected CVR row overlaps with a redaction.

2. **Universe ordering:** The exact ordering of ballots in `compute_sample_ballots()` determines the sample. The observer script must replicate this precisely. Is the ordering stable and documented? (Currently it is deterministic but not explicitly specified.) Should it be formally documented as part of the audit protocol?

3. **Opportunistic contest risk threshold:** When contests are not audited (either targeted or opportunitically) reporting 100% risk is technically correct but may be alarming. The UI should probably explain this by noting that risk for those contests needs to be addressed via another sort of auditing.

4. **Data access for observer scripts:** The observer scripts need access to the exported data. The proposed testing flow should include a design for how to do that, since observers and the public don't have access to the Arlo instance.

5. **Excerpt generation: official tool or observer tool?** The excerpt generator currently uses the CVR — a file that, for rare styles, must be anonymized before public release. The final approach will depend on the anonymization and data access choices noted above. Excerpt generation must come from an observer-side tool that observers generate from the publicly-posted (anonymized) CVR.
