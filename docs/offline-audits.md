# Offline Ballot-Polling Audits and Ballot Multiplicity

Arlo audits can be **online** (audit board members record their
interpretation of each ballot directly in Arlo) or **offline**
(the jurisdiction hand-counts the sampled ballots and enters
aggregate vote totals per contest/choice). This doc covers a subtlety
in offline ballot-polling audits that isn't obvious from the UI:
**ballot multiplicity**.

## Why the same ballot can appear more than once in a sample

Ballot-polling samples are typically drawn *with replacement*, so
the same physical ballot can be selected more than once in a single
round. Each individual draw gets its own ticket number (assigned by
the [`consistent_sampler`](https://github.com/ron-rivest/consistent_sampler)
module), but repeated draws of the same physical ballot all point back
to one physical ballot — there's no second copy to go retrieve.

Statistically, each *draw* still needs to count separately: if a
ballot is drawn twice, its votes must be counted twice toward the
sample's totals. This is what "multiplicity" refers to.

## How multiplicity shows up in the retrieval list

The retrieval list CSV (`GET .../ballots/retrieval-list`) has one row
per unique physical ballot. If a ballot was drawn more than once, its
**Ticket Numbers** column lists all of its ticket numbers, comma
separated (e.g. `3,47`). That comma-count is currently the *only*
signal of multiplicity — there's no dedicated multiplicity/count
column (tracked in
[votingworks/arlo#779](https://github.com/votingworks/arlo/issues/779)).
When tallying by hand or in a spreadsheet built from this list, treat
each ticket number in that column as a separate draw: a ballot with
two ticket numbers contributes its votes twice to the totals you
enter.

## The "Ballots to audit" count vs. the sample size

The jurisdiction admin's round-management screen shows a **"Ballots
to audit"** figure. This is the count of *unique physical ballots* to
retrieve, not the sample size. If any ballots were drawn more than
once, the sample size (number of draws) will be *larger* than this
number.

This matters when entering offline results: Arlo validates that your
entered totals for each contest don't exceed `(sample size) × (votes
allowed)`, where "sample size" is the draw count, *not* the unique
ballot count shown to you. That check is an upper bound only — it
won't flag totals that are too low. So if you tally based on the
"Ballots to audit" figure and forget to double-count any repeated
ballots, Arlo will not warn you that your totals are short.

**Bottom line:** when a jurisdiction reports offline results, make
sure the tally accounts for every *draw* (ticket number) in the
retrieval list, not just every unique physical ballot — a ballot
drawn twice should have its votes counted twice.

## Known gap

Surfacing this more clearly in the product — a real multiplicity
column on the retrieval list, and/or showing the weighted sample size
alongside the unique-ballot count on the round-management screen — is
tracked in
[votingworks/arlo#779](https://github.com/votingworks/arlo/issues/779).
This doc is a stopgap until that's addressed.
