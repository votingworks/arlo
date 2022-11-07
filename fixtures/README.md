# Manual Test Fixtures

This directory contains auto-generated test data that can be used when manually testing Arlo.

Each subdirectory contains all of the files needed to audit one election. These files have randomly generated election results based on an **election specification** defined in that directory (a file ending in `.spec.json`).

## Using a fixture

- Log into Arlo (e.g., using the Support Tools interface at /auth/support/start).
- Create an organization or pick an existing organization
- Log in as an audit admin
- Create a new audit of your desired audit type
- Look in the subdirectory of the election you want to use for the audit. Depending on the audit method, you'll need different files from this subdirectory.

### Ballot Polling

You'll need:

- The jurisdictions file
- The reported election results from the spec file
- The ballot manifest file for each jurisdiction

### Ballot Comparison

You'll need:

- The jurisdictions file
- The standardized contests file
- The CVR file for each jurisdiction
- The ballot manifest file for each jurisdiction

### Batch Comparison

You'll need:

- The jurisdictions file
- The ballot manifest file for each jurisdiction
- The candidate totals by batch file for the contest you want to audit

### Hybrid

Not supported yet!

## Generating a new election

- Create a new subdirectory for your election
- Create an election specification file within that directory
- (Suggested) Use the audit planner (`/planner`) to test out your election results to make sure they give you a workable sample size
- Run `poetry run python generate_election.py <path to your spec file> <path to your subdirectory>`

The `generate_election.py` script uses a fixed random seed and is idempotent, so running it with a given spec file will always produce the same results. If you want to change anything, just change the spec and re-run the script - it will overwrite the existing test files.

If you want some help generating fun random names for your election spec, check out: https://www.fantasynamegenerators.com/, specifically the generators for [town names](https://www.fantasynamegenerators.com/town-names.php) (good for jurisdiction names) and [title names](https://www.fantasynamegenerators.com/title-names.php) (good for contest names).

## Development

### Testing

    poetry run pytest

### Regenerating all elections

You should do this anytime you make a change to the election generation code. (TODO - add a test to enforce this.)

    ./regenerate-all-elections.sh
