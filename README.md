# Arlo: Open-source risk-limiting audit software by [VotingWorks](voting.works)

Arlo is a web-based [risk-limiting audit (RLA)](https://risklimitingaudits.org) tool used to conduct post-election audits in the United States.  The tool helps election officials complete a statistically valid audit of vote tabulation processes by comparing the votes marked on a random sample of original paper ballots with the electronically recorded votes for those same ballots. This type of audit can confirm that the reported winner did indeed win, or correct the outcome through a full hand recount if the reported outcome cannot be confirmed.

## About Arlo

As part of the audit, Arlo:

* Uses basic election data to determine how many ballots should be examined

* Randomly selects individual ballots to be examined from a list of all ballots cast in particular contest(s), and provides auditors with the information they need to find those ballots in storage

* Provides supplemental materials necessary to maintain chain of custory while retrieving ballots

* Checks whether votes recorded by auditors examining each ballot match what we would expect if the reported outcome is correct, more specifically whether the desired risk-limit has been achieved based on these results

  * If not, randomly selects additional ballots to expand the sample size and continue the audit, up to a full hand recount if necessary

* Provides monitoring & reporting so that election officials and public observers can follow the progress and outcome of the audit

### Supported election types, audit methods, and processes

Arlo currently supports ballot polling risk-limiting audits of single or multi-winner plurality contests. Only one targeted contest is supported at this time, although mutliple instances of the tool may also be run in parallel if multiple targeted contests are desired. If multiple jurisdictions are participating in the audit, ballot manifests and vote/ballot totals for each jurisdiction must be manually combined. Votes from individual audited ballots are currently recorded & tallied manually, then entered into the tool as totals. 

### Statistical methods

Arlo uses the BRAVO ballot polling method of measuring risk and estimating how many ballots need to be examined ([Lindeman et al, 2012](https://www.usenix.org/system/files/conference/evtwote12/evtwote12-final27.pdf)). 

Random sampling of ballots is done using [Rivest's Consistent Sampler](https://github.com/ron-rivest/consistent_sampler). 

### Required source data

To run a basic ballot polling audit you will need: 

  * Election name (string, e.g. "November 2019 General Election)
  
  * Targeted contest name (string, e.g. "Constitutional Amendment 1a")
  
  * Candidate/choice names for the targeted contest (strings, e.g. "Ann Marie Smith" or "Yes/Approve")
  
  * Vote totals for each candidate/choice (integers, e.g. "453")
  
  * Total ballot cards/pages cast (integer, e.g. "10023")
    * Note that this is *total ballot cards/pages* rather than total ballots - if you have a single-page ballot those numbers will be the same, but if you have a multi-page ballot each page is counted individually. For example, if 1000 two-page ballots are cast, the total ballot card/page count is 2000.
    
  * Ballot manifest file, listing all the batches of ballots in storage and how many ballot pages/cards are stored in each batch (see file format requirements below)

### Ballot manifest file format

The Ballot Manifest file must:

  * Be a comma-separated file saved in .csv format
  
  * Contain a header row with two column headers, labeled "Batch Name" and "Number of Ballots"
  
  ![Example ballot polling ballot manifest](https://github.com/votingworks/arlo/blob/readme-updates/images/Ballot%20Manifest%20Example.png)

Note that batch names are strings with no required naming conventions - use whatever names or IDs are normally associated with your ballot storage batches/containers. "Number of Ballots" should be an integer, and is *the number of ballot pages/cards* in each ballot storage batch. 

### Future development

Ongoing development is planned to support:

  * Ballot-by-ballot data entry
   
  * Multiple targeted contests 
  
  * Distributed multi-jurisdiction contests
  
  * Batch comparison RLAs
  
  * Ballot comparison RLAs
  
  * Public audit dashboard
  
  * Additional election types (proportional contests, etc.)
  
  * More efficient statitstical methods

## Developer resources

Arlo is open-source software ([AGPL v3.0](https://github.com/votingworks/arlo/blob/master/LICENSE)), meaning you are free to use it, modify it, and redistribute those modifications as you'd like, provided that, when you redistribute your modifications, you share them in the same open way. Because Arlo is open-source, anyone can review it or run their own copy, thus ensuring that, when used in a real audit, it is performing according to specification.

Like any open-source software, Arlo welcomes suggested changes in the form of pull requests on GitHub. If you're interested in getting a change merged into Arlo, please consider the following:

* test coverage is mandatory. We won't merge code without it.

* significant / risky changes may take some time to review, and are not likely to be merged unless they've been discussed first. The stability of Arlo is a prime concern. A good way to start a conversation around a large change is by opening up a ticket.

* we really want to know about anything that gets in the way of installing and using Arlo. Please file tickets, suggest changes to our installation instructions, etc.

### Setting up the dev environment

1. Download [`python-dev`](https://www.python.org/) >3.7 
2. Download [`pip`](https://pypi.org/project/pip/)
3. Install `pipenv` (note: run `python3 -m pip install pipenv` to get a version that's compatible with your local python install if your system defaults to a python other than >3.7).
4. Install [`yarn`](https://yarnpkg.com/en/docs/install).
5. Install `postgres-client` and `postgresql-dev`, see https://www.postgresql.org/download.
6. Install dependencies with `make install` or `make install-development` depending on your use-case
7. Create a database config by copying `config/database.cfg.example` to `config/database.cfg`
8. Run tests via `make test-sever`
9. Run via `./run-dev.sh`

### Troubleshooting

* Postgres is best installed by grabbing `postgresql-server-dev-10` and `postgresql-client-10`.
* `psychopg2` has known issues depending on your install (see, e.g., [here](https://github.com/psycopg/psycopg2/issues/674)). If you run into issues, switch `psychopg2` to `psychopg2-binary` in the Pipfile
* `pipenv install` can hang attempting to get [a lock on the packages it's installing](https://github.com/pypa/pipenv/issues/3827). To get around this, add the `--skip-lock` flag in the Makefile (the first line should be `pipenv install --skip-lock`).
* A password may have to be set in `config/database.cfg` depending on your install of postgres. To do this, change  `postgres://postgres@localhost:5432/arlo` to `postgres://postgres:{PASSWORD}@localhost:5432/arlo`, replacing `{PASSWORD}` with the password.
* You may need to create an `arlo` and `arlo-test` databases manually [via postgres](https://www.postgresql.org/docs/9.0/sql-createdatabase.html). 
