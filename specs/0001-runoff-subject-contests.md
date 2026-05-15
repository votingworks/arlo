# Plan: Audit the Majority Claim for Runoff-Subject Contests (Batch Comparison)

## Context

Georgia is Arlo's only customer that conducts batch comparison audits (MACRO) of primary contests subject to **majority-or-runoff** law: if a candidate receives a majority of valid votes they win the primary outright; otherwise the top two advance to a runoff. Arlo today only audits the pairwise margins (the declared winner beats every other candidate). It does _not_ statistically verify the majority claim — i.e., whether the reported leader's share actually does or does not cross 50%.

That leaves a gap in both directions:

- If the reported leader is under 50% (runoff stands), Arlo doesn't confirm "no one actually hit a majority." A miscount could mean a candidate truly won outright and a runoff is being held that shouldn't be.
- If the reported leader is at or over 50% (no runoff), Arlo doesn't confirm "they really did reach a majority." A miscount could mean the announced winner doesn't actually have a majority, and a runoff _is_ legally required.

This plan adds the missing verification. From the user's perspective, the contest is always a single-winner contest; a checkbox marks it as subject to runoff law. The math module internally handles both the "primary winner declared" and the "top-2 advance to runoff" cases based on the reported tallies.

- **No reported majority** (top two advance to a runoff): audit that **each** of the two reported top candidates received under 50% of valid votes, _and_ that the reported runner-up R genuinely beats every non-advancing candidate. The existing pairwise math only pairs the declared winner W against the rest — so without extra assertions, R's standing as runner-up isn't audited.
- **Reported majority** (single primary winner, no runoff): audit that the reported leader did in fact receive at least 50% of valid votes.

### Notation

Notation matches the existing function and the MACRO paper:

- `v_wp` = reported votes for the **w**inner in batch **p**.
- `v_lp` = reported votes for the **l**oser in batch **p**.
- `a_wp`, `a_lp` = the same as above but for **a**udited votes (from `sampled_results`).
- `V_wl` = global reported margin between **w**inner and **l**oser across the whole contest.

### Math reframe (the key insight)

_Human-speak version_ -

Right now we `compute_error` for batch comparison contests [here](https://github.com/votingworks/arlo/blob/main/server/audit_math/macro.py#L54) in the macro module. The core of the process is that we have a list of winners and a list of losers. For each winner-loser pair, we calculate a batch error. We then return the max error across each winner-loser pair to determine the error for that batch. We then use that error to determine the taint, which is the main contributor to calculating that batch's contribution to risk. Finally, we multiply the per-batch risk contributions to get the combined risk, the p-value.

To add support for validating a contest that is subject to runoff rules, we need to validate 1 or 2 additional assertions.

If the votes indicate one candidate received >50% of the votes, we need to validate that a runoff is not needed by adding that as an additional assertion. A clever way to add this assertion that fits relatively neatly into our existing model in the macro module is to model this threshold assertion as follows: assert the winner `W` has more votes than all other candidates, i.e. `not-W`, as this would assert the winner had more than 50% of votes.

If the votes indicate no candidate received >50% of the votes, we need to validate the runoff is indeed required. First, we model this contest as having two winners, as the existing audit math will validate that top_vote_getter and second_vote_getter are indeed the two candidates that should be going to the runoff. In essence, there are two winners. Next, we need 2 additional assertions - that neither of these two candidates received more than 50% of the votes. We can use the same clever modeling described in the previous paragraph, just reversed. We assert these threshold assertions by asserting that `not-W` had more votes than `W` for each of the two top vote getters.

Now, the max error of the existing candidate pair assertions and these new threshold assertions is selected in calculating each batch's error, which is how they will contribute to the audit's `p-value`.

Note: An interesting consequence of adding these threshold assertions is that we may see them be the driving factor of sample size if the top candidate is close to having 50% of the total vote. Previously if the main contribution to risk was a candidate that had 51% of the vote having 31% more than the second candidate having 20% of the vote, that risk will now be dominated by the assertion that the winner had 51% of the vote compared to the not-winners having 49% of the vote, clearly a much tighter margin.

These additional assertions will also be used in `compute_max_error` along with the existing candidate pair assertions to determine the upper bound of overstatement that a batch could contribute, used to drive sampling.

_AI-speak technical version_ -

Threshold assertions (real candidate vs aggregate candidate) are represented as **explicit, self-contained pair entries** in a new `contest.runoff_pairs` collection. The aggregate side of a threshold pair (`__not_W`) has its per-batch tally pre-computed (sum of all real-candidate tallies in that batch, minus W's tally) before MACRO iterates. In the no-majority case, the runner-up R is additionally promoted into `self.winners` (with `self.num_winners` set to 2) so the existing pairwise winner×loser iteration validates R's standing against every non-advancing candidate — no extra entries needed for those pairs. MACRO iterates the threshold entries with the same arithmetic and produces a single p-value covering everything. Implementation details — including the structural-winner direction rule and the `V_wl ≥ 0` invariant — are in Section 2.

### Design decisions

- **Field name**: `is_subject_to_runoff` (boolean) on `Contest`. Captures the domain reality: this contest is governed by majority-or-runoff law. When on, the audit verifies the majority claim and (in the no-majority case) the runner-up's standing.
- **`num_winners` constraint**: the flag is only valid when `num_winners == 1`. From the user's perspective a primary subject to runoff law is conceptually a single-winner race (one candidate wins outright if they hit majority; otherwise a runoff later decides between the top two). The "two winners advance to a runoff" framing is a math-internal concern in the no-majority case — it doesn't surface in the DB, API, form, or report.
- **Audit type scope**: `BATCH_COMPARISON` only for v1. Other audit types raise a validation error if the flag is set.
- **UI surfacing**: Checkbox appears on the contest form whenever `Election.state == "GA"` and `audit_type == BATCH_COMPARISON`. It is disabled (and forced off) when `numWinners != 1`, so the relationship between the flag and the `num_winners` constraint is visible to the user rather than hidden. Defaults to off.
- **Both majority and no-majority directions are valid audit configurations.** The math handles either; the audit doesn't reject contests based on which side of 50% the reported leader is on. The direction is derived inside the math module from `contest.candidates`.

### Open questions to confirm before implementation

**MACRO conservative-adjustment composability with aggregate candidates** (math review needed):

The threshold check is modeled as a pairwise pair between a real candidate W and an aggregate candidate `not-W` (whose reported tally = sum of all other real candidates' tallies). The structural "winner" of the pair is whichever side has more reported votes, so `V_wl ≥ 0` by construction (exact tie will degrade to a hand recount via MACRO's existing `V_wl ≤ 0` guard). The per-batch error and max-error arithmetic is identical to MACRO's existing pairwise math, except `V_wl` is sourced from the assertion's own tallies rather than from `contest.candidates`.

- Does MACRO's existing single-subtract of `pending_ballots` and `unauditable_ballots` from `V_wl` still hold when one side of the pair is a sum-of-others rather than a single real candidate — in both directions (majority case: real candidate is the winner, `not-W` is the loser; no-majority case: `not-W` is the winner, real candidate is the loser)?
- Does the presence of undervoted ballots — which appear in batch ballot counts but in no candidate's tally, and therefore aren't in `not-W` either — require any additional adjustment specifically to the threshold-pair math?

### Reference: Georgia majority definition

Ga. Code § 21-2-501: a runoff is required if no candidate receives **more than 50%** of the vote. The comparison throughout the plan (math direction, backend validation) uses strict `> 0.5` accordingly.

---

## Implementation

### 1. Database — add the flag

**[server/models.py:468](../server/models.py#L468)** — add to `Contest`:

```python
# When True, this contest is governed by majority-or-runoff law: a
# candidate wins outright if they receive a strict majority of valid
# votes, otherwise the top two advance to a runoff. The audit verifies
# the reported majority claim (and the runner-up's standing, in the
# no-majority case). Only valid for batch comparison audits with
# num_winners == 1.
is_subject_to_runoff = Column(Boolean, nullable=False, server_default="false")
```

**New migration** in [server/migrations/versions/](../server/migrations/versions/) — follow [7ca7a4b0bcc0_contest_pending_ballots.py](../server/migrations/versions/7ca7a4b0bcc0_contest_pending_ballots.py):

```python
def upgrade():
    op.add_column(
        "contest",
        sa.Column("is_subject_to_runoff", sa.Boolean(), nullable=False, server_default="false"),
    )
```

### 2. Math — synthesize threshold and runner-up assertions inside the math module

The entire "two winners advance in the no-majority case" treatment lives here. The DB, API, and form all see `num_winners=1`; the math module privately derives the appropriate assertions from `contest.candidates`.

**[server/audit_math/sampler_contest.py](../server/audit_math/sampler_contest.py)** — changes:

1. `from_db_contest` (line 21): add `"isSubjectToRunoff": db_contest.is_subject_to_runoff` to `info_dict`.
2. `Contest.__init__` (line 70): read `self.is_subject_to_runoff = contest_info_dict.get("isSubjectToRunoff", False)`; add the key to the skip-keys list at line 80.
3. Inside `Contest.__init__`, add two blocks around the existing margin-population block ([sampler_contest.py:113-160](../server/audit_math/sampler_contest.py#L113-L160)).

   The first block, **before** margin-population, decides direction: if `self.is_subject_to_runoff` and no candidate has a strict majority, set `self.num_winners = 2` so the existing winner-detection loop puts both top candidates into `self.winners` (and their pairwise margins fall out of the margin-population block automatically).

   The second block, **after** margin-population, builds `self.runoff_pairs` — a `list[dict]` with shape `{"winner_id", "winner_votes", "loser_id", "loser_votes"}` — by emitting one threshold pair per entry in `self.winners`:

   ```python
   # Before the existing margin-population block:
   if self.is_subject_to_runoff:
       total_valid = sum(self.candidates.values())
       top_votes = max(self.candidates.values())
       if top_votes <= total_valid - top_votes:
           # No-majority case (incl. exact 50/50): treat as 2-winner internally.
           self.num_winners = 2

   # ... existing margin-population block runs unchanged ...

   # After the existing margin-population block:
   if self.is_subject_to_runoff:
       total_valid = sum(self.candidates.values())
       runoff_pairs: list[dict] = []
       for w_id, w_votes in self.winners.items():
           not_id = f"__not_{w_id}"
           not_votes = total_valid - w_votes
           if w_votes > not_votes:
               # Majority case for this winner: assert W > not-W.
               runoff_pairs.append({
                   "winner_id": w_id, "winner_votes": w_votes,
                   "loser_id":  not_id, "loser_votes": not_votes,
               })
           else:
               # No-majority case for this winner: assert not-W > W.
               runoff_pairs.append({
                   "winner_id": not_id, "winner_votes": not_votes,
                   "loser_id":  w_id, "loser_votes": w_votes,
               })
       self.runoff_pairs = runoff_pairs
   ```

   Direction rule for threshold pairs: the structural "winner" is whichever side has more reported votes, ensuring `V_wl ≥ 0`. At exact 50/50, `V_wl = 0` and MACRO's existing guard forces a hand recount — the correct fallback (zero reported margin cannot be statistically distinguished from a true majority or shortfall). Aggregate candidates (`__not_W`, `__not_R`) live exclusively in `self.runoff_pairs` — they are not added to `self.winners` or `self.losers`.

**[server/audit_math/macro.py](../server/audit_math/macro.py)** — changes:

1. Add a helper `add_aggregate_tallies(contest, results_by_batch)` that mutates the input dict: for each batch's per-contest entry, adds a `__not_<X>` key for every aggregate ID referenced in `contest.runoff_pairs`, with value `sum_of_real_candidates_in_batch − X_votes_in_batch`. Skip any batch where `contest.name` is not present (mirrors the existing `if contest.name not in sample_results[batch]: continue` check at [macro.py:345](../server/audit_math/macro.py#L345)). Assignment-based (idempotent) so that double-augmentation through `get_sample_sizes → compute_risk` is harmless — only mutates if `contest.is_subject_to_runoff`.
2. Call `add_aggregate_tallies` at the top of MACRO's two public entry points — `get_sample_sizes` ([macro.py:209](../server/audit_math/macro.py#L209)) on `reported_results`, and `compute_risk` ([macro.py:287](../server/audit_math/macro.py#L287)) on both `reported_results` and `sample_results`. After these calls, every downstream lookup of `batch_results[contest.name][__not_<X>]` resolves to a real number.
3. In `compute_error` at [macro.py:106-114](../server/audit_math/macro.py#L106-L114), after the existing `error_for_candidate_pair` list comprehension, append errors from each runoff assertion:
   ```python
   maybe_errors += [
       error_for_runoff_pair(p) for p in contest.runoff_pairs
   ]
   ```
4. Add `error_for_runoff_pair(pair)` next to [`error_for_candidate_pair`](../server/audit_math/macro.py#L82). Same arithmetic, but `V_wl` is read from `pair["winner_votes"] - pair["loser_votes"]` rather than from `contest.candidates`. Returns the same `BatchError` shape so the surrounding `max(...)` aggregation just works. (May be simpler to refactor `error_for_candidate_pair` to accept `(winner_id, loser_id, V_wl)` directly and drive both iterations through it.)
5. In `compute_max_error` at [macro.py:147-172](../server/audit_math/macro.py#L147-L172), same change: add a parallel inner loop over `contest.runoff_pairs` calling a sibling `max_error_for_runoff_pair(pair)` (same `((v_wp − v_lp) + b_cp) / V_wl` shape, where `b_cp` is the total **b**allot count for the **c**ontest in batch **p**, read from `batch_results[contest.name]["ballots"]`).

The `__not_` prefix is purely an ID-naming convention — correctness comes from the assertion list being closed over its own `(winner_id, loser_id, V_wl)` tuples, not from any string matching. Aggregate candidates are a math-module concern and stay inside `macro.py` + `sampler_contest.py`.

### 3. API ingest — schema, validation, serialization

**[server/api/contests.py](../server/api/contests.py)**:

1. `CONTEST_SCHEMA` ([contests.py:28](../server/api/contests.py#L28)): add `"isSubjectToRunoff": {"type": "boolean"}` to properties. Not required (defaults to false).
2. `validate_contests` ([contests.py:237](../server/api/contests.py#L237)): add a check — for each contest with `isSubjectToRunoff == True`:
   - Election audit type must be `BATCH_COMPARISON` → else `BadRequest("Runoff-subject contests are only supported for batch comparison audits")`.
   - `numWinners` must be `1` → else `BadRequest("Runoff-subject contests must have num_winners=1")`.
   - At least 3 choices. With only 2 choices the contest is already a head-to-head race and the threshold pair degenerates to the head-to-head pair.
3. `serialize_contest` ([contests.py:127](../server/api/contests.py#L127)): include `"isSubjectToRunoff": contest.is_subject_to_runoff` only when `audit_type == BATCH_COMPARISON` (mirroring how `pendingBallots` is conditionally serialized at line 138).
4. `deserialize_contest` ([contests.py:222](../server/api/contests.py#L222)): pass through `is_subject_to_runoff=contest.get("isSubjectToRunoff", False)`.

### 4. UI — contest form

**[client/src/components/AuditAdmin/Setup/Contests/ContestForm.tsx](../client/src/components/AuditAdmin/Setup/Contests/ContestForm.tsx)**:

- Add `isSubjectToRunoff: boolean` to `IContestValues` (around line 190).
- Render a Blueprint `Checkbox` labeled e.g. "Subject to runoff law" — shown whenever the audit's state is `"GA"` and the audit type is `BATCH_COMPARISON`. Place it near the `numWinners` field. The audit state is available from the election context already used in the form.
- Disable the checkbox (and force its value to `false`) when `numWinners != 1`. Add a short helper line in that disabled state explaining why, e.g. _"Only available for single-winner contests."_ This keeps the constraint discoverable rather than hidden.
- When the checkbox is on, display a short contextual line under it describing what the audit will verify, derived from the candidate vote inputs already on the same form:
  - Compute `totalValid = sum(numVotes for each choice)` and `leaderShare = max(numVotes) / totalValid`. Recompute on blur of any candidate-vote input, and only when every choice row has both a name and a vote total filled in.
  - If `leaderShare > 0.5` (strict majority, per Ga. Code § 21-2-501): `"Reported results: {leader.name} received a majority, no runoff required."`
  - Otherwise: `"Reported results: {leader.name} and {runner_up.name} are the top two vote-getters and neither received a majority, runoff required."`
  - Blank before the first successful computation.
- Add `isSubjectToRunoff: Yup.boolean()` to [schema.ts](../client/src/components/AuditAdmin/Setup/Contests/schema.ts).

### 5. Audit report CSV — surface the outcome

The audit admin's CSV report ([server/api/reports.py:400](../server/api/reports.py#L400)) is the canonical place audit results land. Per-contest p-values and `is_complete` already appear in the "ROUNDS" section; we extend that section with a single outcome column for flagged contests.

- **Conditionally add a "Runoff Outcome" column** to the `ROUNDS` header alongside the existing batch-comparison-only columns at [reports.py:419-422](../server/api/reports.py#L419). The column appears only when `any(contest.is_subject_to_runoff for contest in election.contests)`. For audits with no flagged contests (the common case), the CSV looks identical to today.
- **Populate the cell** in `round_rows` at [reports.py:534-563](../server/api/reports.py#L534) based on the reported tallies (since `num_winners` is always 1 for flagged contests, the direction is derived from `contest.candidates`):
  - `""` if the contest doesn't have the flag set (but the audit has other contests that do, so the column exists).
  - `"Majority confirmed"` if `is_complete` is True and the declared winner's reported tally is a strict majority of valid votes.
  - `"No majority — runoff required"` if `is_complete` is True and the declared winner's reported tally is not a strict majority.
  - `""` if `is_complete` is False — the existing "Risk Limit Met?" column already says No, and no outcome can be claimed.

### 6. Tests

**[server/tests/audit_math/test_sampler_contest.py](../server/tests/audit_math/test_sampler_contest.py)** — new tests:

- `test_runoff_no_majority_pairs`: 4-candidate contest 40/35/15/10 with `isSubjectToRunoff=True` and `numWinners=1`. Asserts:
  - `contest.num_winners == 2` and `contest.winners` contains both Alice and Bob (runner-up promoted), `contest.losers` contains only Carla and Dan.
  - `contest.runoff_pairs` has exactly two entries — `not_W > W` and `not_R > R` — both with `winner_votes > loser_votes`. (R-vs-non-advancing pairs are validated by the existing winner×loser iteration, not via this list.)
- `test_runoff_majority_pairs`: 4-candidate contest 55/25/15/5 with the flag on and `numWinners=1`. Asserts `runoff_pairs` has one entry: `W > not_W` with `winner_votes > loser_votes`.

**[server/tests/audit_math/test_macro.py](../server/tests/audit_math/test_macro.py)** — new tests, follow the existing fixture style at [test_macro.py:12-101](../server/tests/audit_math/test_macro.py#L12):

- `test_runoff_no_majority_happy_path`: 4-candidate contest, reported 40/35/15/10, batches consistent with reported. All assertions clear — W and R each vs every non-advancing loser (existing pairwise math with the internal `num_winners=2` promotion), plus the `not_W > W` and `not_R > R` threshold pairs. Audit terminates.
- `test_runoff_majority_happy_path`: 4-candidate contest, reported 55/25/15/5, batches consistent. Existing pairs (leader vs every other candidate) plus the `W > not-W` threshold pair clear. Audit terminates.
- `test_runoff_threshold_dominates_sample_size`: reported leader at 48% — confirm sample size is materially larger than with the flag off (threshold pair becomes binding).
- `test_runoff_discrepancy_flips_majority`: reported leader at 51%, but introduce sampled batch discrepancies that, scaled up, would put the leader under 50%. Risk fails to clear and the audit doesn't terminate (escalation/full hand-count expected).

**[server/tests/api/test_contests.py](../server/tests/api/test_contests.py)** — new tests:

- `test_runoff_flag_serialized_for_batch_comparison`: PUT-then-GET round trip preserves the flag.
- `test_runoff_flag_rejected_for_non_batch_comparison`: 400 with a clear message for ballot polling, ballot comparison, hybrid.
- `test_runoff_flag_rejects_num_winners_not_one`: 400 if `numWinners != 1`.
- `test_runoff_flag_requires_three_or_more_choices`: 400 with 2 choices.

**[server/tests/api/test_reports.py](../server/tests/api/test_reports.py)** — new tests (confirm the existing report-test file location before adding):

- `test_audit_report_runoff_outcome_no_majority`: completed flagged contest, reported tallies Alice 40 / Bob 35 / Carla 15 / Dan 10 — CSV's "Runoff Outcome" cell reads `"No majority — runoff required"`.
- `test_audit_report_runoff_outcome_majority`: completed flagged contest, reported tallies Alice 55 / Bob 25 / Carla 15 / Dan 5 — cell reads `"Majority confirmed"`.
- `test_audit_report_runoff_outcome_blank_for_non_flagged_in_same_audit`: an audit with at least one flagged contest and one non-flagged contest — the column is present, the flagged contest's cell is populated, the non-flagged contest's cell is empty.
- `test_audit_report_runoff_outcome_column_absent_when_no_contest_flagged`: an audit with no flagged contests — the "Runoff Outcome" column does not appear in the CSV at all.
- `test_audit_report_runoff_outcome_blank_when_incomplete`: flagged contest, `is_complete=False` — cell is empty (the existing "Risk Limit Met?" column says No).

---

## Verification

1. **Run the math tests**:
   ```
   pytest server/tests/audit_math/test_sampler_contest.py server/tests/audit_math/test_macro.py -v
   ```
2. **Run the API tests**:
   ```
   pytest server/tests/api/test_contests.py -v -k runoff
   ```
3. **Migration**:
   ```
   make resetdb && alembic upgrade head
   ```
   Then inspect that `contest.is_subject_to_runoff` exists and defaults to false.
4. **Manual end-to-end** (frontend dev server + backend):
   - Create a new audit, state=Georgia, type=Batch Comparison.
   - Confirm the new checkbox appears on the contest form for Georgia batch comparison audits. It should not appear for other states or non-batch-comparison audit types. When `numWinners != 1`, it should be disabled with a helper line explaining the constraint.
   - Configure a contest with 4 candidates, `numWinners=1`, reported tallies summing such that the leader is at 40%. Check the box. Contextual line should read e.g. _"Reported results: Alice and Bob are the top two vote-getters and neither received a majority, runoff required."_ Submit — succeed.
   - Without unchecking the box, change one candidate's votes so the leader is now at 55%. Contextual line should flip to _"Reported results: Alice received a majority, no runoff required."_ Submit — also succeed.
   - Upload batch tallies and launch the audit.
   - Run a round, enter audit-board results consistent with the reported tallies, confirm the round closes successfully and the displayed p-value covers all assertions.
   - **Download the audit report CSV** and verify the new "Runoff Outcome" column reads `"No majority — runoff required"` or `"Majority confirmed"` depending on the reported tallies.
5. **Negative manual cases** — verify that the API rejects (400 with clear message):
   - Submitting a non-batch-comparison audit with the flag.
   - Submitting a contest with `numWinners=2` and the flag.

---

## Files touched (summary)

| Layer                         | Path                                                                                                                                                                                               |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DB model                      | [server/models.py:468](../server/models.py#L468)                                                                                                                                                   |
| Migration                     | `server/migrations/versions/<new_id>_contest_is_subject_to_runoff.py`                                                                                                                              |
| Math (contest object)         | [server/audit_math/sampler_contest.py](../server/audit_math/sampler_contest.py)                                                                                                                    |
| Math (MACRO runoff iteration) | [server/audit_math/macro.py:106-114](../server/audit_math/macro.py#L106-L114), [macro.py:147-172](../server/audit_math/macro.py#L147-L172)                                                         |
| API schema / validation       | [server/api/contests.py:28](../server/api/contests.py#L28), [contests.py:237](../server/api/contests.py#L237)                                                                                      |
| API (de)serialization         | [server/api/contests.py:127](../server/api/contests.py#L127), [contests.py:222](../server/api/contests.py#L222)                                                                                    |
| Audit report CSV              | [server/api/reports.py:400](../server/api/reports.py#L400), [reports.py:534-563](../server/api/reports.py#L534-L563)                                                                               |
| UI form                       | [client/.../ContestForm.tsx](../client/src/components/AuditAdmin/Setup/Contests/ContestForm.tsx)                                                                                                   |
| UI schema                     | [client/.../schema.ts](../client/src/components/AuditAdmin/Setup/Contests/schema.ts)                                                                                                               |
| Tests                         | [test_sampler_contest.py](../server/tests/audit_math/test_sampler_contest.py), [test_macro.py](../server/tests/audit_math/test_macro.py), [test_contests.py](../server/tests/api/test_contests.py) |
