# Arlo: Open-source risk-limiting audit software by [VotingWorks](https://voting.works)

Arlo is a web-based [risk-limiting audit (RLA)](https://risklimitingaudits.org) tool used to conduct post-election audits in the United States. The tool helps election officials complete a statistically valid audit of vote tabulation processes by comparing the votes marked on a random sample of original paper ballots with the electronically recorded votes for those same ballots. This type of audit can confirm that the reported winner did indeed win, or correct the outcome through a full hand recount if the reported outcome cannot be confirmed.

## About Arlo

As part of the audit, Arlo:

- Uses basic election data to determine how many ballots should be examined

- Randomly selects individual ballots to be examined from a list of all ballots cast in particular contest(s), and provides auditors with the information they need to find those ballots in storage

- Provides supplemental materials necessary to maintain chain of custody while retrieving ballots

- Checks whether votes recorded by auditors examining each ballot match what we would expect if the reported outcome is correct, more specifically whether the desired risk-limit has been achieved based on these results

  - If not, randomly selects additional ballots to expand the sample size and continue the audit, up to a full hand recount if necessary

- Provides monitoring & reporting so that election officials and public observers can follow the progress and outcome of the audit

### Supported election types, audit methods, and processes

Arlo currently supports ballot polling risk-limiting audits of single or multi-winner plurality contests. Only one targeted contest is supported at this time, although mutliple instances of the tool may also be run in parallel if multiple targeted contests are desired. If multiple jurisdictions are participating in the audit, ballot manifests and vote/ballot totals for each jurisdiction must be manually combined. Votes from individual audited ballots are currently recorded & tallied manually, then entered into the tool as totals.

### Statistical methods

Arlo uses the BRAVO ballot polling method of measuring risk and estimating how many ballots need to be examined ([Lindeman et al, 2012](https://www.usenix.org/system/files/conference/evtwote12/evtwote12-final27.pdf)).

Random sampling of ballots is done using [Rivest's Consistent Sampler](https://github.com/ron-rivest/consistent_sampler).

### Required source data

To run a basic ballot polling audit you will need:

- Election name (string, e.g. "November 2019 General Election)

- Targeted contest name (string, e.g. "Constitutional Amendment 1a")

- Candidate/choice names for the targeted contest (strings, e.g. "Ann Marie Smith" or "Yes/Approve")

- Vote totals for each candidate/choice (integers, e.g. "453")

- Total ballot cards/pages cast (integer, e.g. "10023")

  - Note that this is _total ballot cards/pages_ rather than total ballots - if you have a single-page ballot those numbers will be the same, but if you have a multi-page ballot each page is counted individually. For example, if 1000 two-page ballots are cast, the total ballot card/page count is 2000.

- Ballot manifest file, listing all the batches of ballots in storage and how many ballot pages/cards are stored in each batch (see file format requirements below)

### Ballot manifest file format

The Ballot Manifest file must:

- Be a comma-separated file saved in .csv format

- Contain a header row with two column headers, labeled "Batch Name" and "Number of Ballots"

![Example ballot polling ballot manifest](https://github.com/votingworks/arlo/blob/readme-updates/images/Ballot%20Manifest%20Example.png)

Note that batch names are strings with no required naming conventions - use whatever names or IDs are normally associated with your ballot storage batches/containers. "Number of Ballots" should be an integer, and is _the number of ballot pages/cards_ in each ballot storage batch.

### Future development

Ongoing development is planned to support:

- Ballot-by-ballot data entry

- Multiple targeted contests

- Distributed multi-jurisdiction contests

- Batch comparison RLAs

- Ballot comparison RLAs

- Public audit dashboard

- Additional election types (proportional contests, etc.)

- More efficient statitstical methods

## Developer resources

Arlo is open-source software ([AGPL v3.0](https://github.com/votingworks/arlo/blob/master/LICENSE)), meaning you are free to use it, modify it, and redistribute those modifications as you'd like, provided that, when you redistribute your modifications, you share them in the same open way. Because Arlo is open-source, anyone can review it or run their own copy, thus ensuring that, when used in a real audit, it is performing according to specification.

Like any open-source software, Arlo welcomes suggested changes in the form of pull requests on GitHub. If you're interested in getting a change merged into Arlo, please consider the following:

- test coverage is mandatory. We won't merge code without it.

- significant / risky changes may take some time to review, and are not likely to be merged unless they've been discussed first. The stability of Arlo is a prime concern. A good way to start a conversation around a large change is by opening up a ticket.

- we really want to know about anything that gets in the way of installing and using Arlo. Please file tickets, suggest changes to our installation instructions, etc.

Before submitting a pull request, please review our [Contribution Guidelines](./docs/contribution-guidelines.md).

### Configuration

[Auth0](https://auth0.com/) is used for authentication, as documented at [Auth0](docs/auth0.md).

Arlo is configured mostly through environment variables:

- `FLASK_ENV`: [environment](https://flask.palletsprojects.com/en/1.1.x/config/#environment-and-debug-features) for the Flask server
- `DATABASE_URL`: PostgreSQL database url, e.g. postgresql://localhost:5342/arlo.
- `ARLO_SESSION_SECRET`: the secret key used to encrypt/auth client-side cookie sessions
- `ARLO_HTTP_ORIGIN`: the proper HTTP/HTTPS origin where this Arlo server is running, e.g. https://arlo.example.com:8443 (as any web origin, no trailing slash)
- `ARLO_AUDITADMIN_AUTH0_BASE_URL`, `ARLO_AUDITADMIN_AUTH0_CLIENT_ID`, `ARLO_AUDITADMIN_AUTH0_CLIENT_SECRET`: base url, client id, and client secret for the auth0 app used for audit admins.
- `ARLO_JURISDICTIONADMIN_AUTH0_BASE_URL`, `ARLO_JURISDICTIONADMIN_AUTH0_CLIENT_ID`, `ARLO_JURISDICTIONADMIN_AUTH0_CLIENT_SECRET`: base url, client id, and client secret for the auth0 app used for jurisdiction admins.
- `ARLO_SUPPORT_AUTH0_BASE_URL`, `ARLO_SUPPORT_AUTH0_CLIENT_ID`, `ARLO_SUPPORT_AUTH0_CLIENT_SECRET`: base url, client id, and client secret for the auth0 app used for support users.
- `ARLO_SUPPORT_EMAIL_DOMAIN`: required email address domain for support users

Rather than manually config the environment, you can also run the setup script discussed below.

### Creating Organizations and Administrators

Organizations are, for example, the State of
Massachusetts. Administrators are individual users that administer
audits for an organization. All authentication is done via auth0 with
email addresses, so users in the Arlo database also need to be
mirrored in the appropriate auth0 tenant user database.

To create an organization in the database:

`pipenv run python -m scripts.create-org <org_name>`

which returns the `organization_id`.

Then, to create an administrator for the organization:

`pipenv run python -m scripts.create-admin <org_id> <admin_email>`

which returns the `user_id`.

### Resetting the Database When Upgrading Arlo

If you're upgrading Arlo, right now the only way is to destroy and
recreate the database. The easiest way to do that, if your database
connection is set up properly, is:

`make resetdb`

If you're running on Heroku or on another system where database
destruction and recreation cannot be done from Python, because the
database is provisioned externally, the steps are then:

- clear the database, e.g. on heroku `heroku pg:reset -a <app_name>`
- create just the data model, e.g. on heroku `heroku run -a <app_name> python -m scripts.resetdb --skip-db-creation`
- you may need to restart servers, e.g. on heroku `heroku restart -a <app_name>`

### Setting up the dev environment

#### Linux

We recommend Ubuntu 18.0.4.

- Install Node10. See https://joshtronic.com/2018/05/08/how-to-install-nodejs-10-on-ubuntu-1804-lts/
- `make dev-environment` or, if you prefer, look at individual make tasks like `deps`, `initdevdb`, `install-development`, and `resetdb`
- `bash ./run-dev.sh`

#### Automatic configuration and setup

If you would just like to run Arlo and do not wish to setup a custom configuration, you can run `pipenv run python -m scripts.setup-dev`, which provides interactive configuration. The script optionally installs VotingWorks' [nOAuth](https://github.com/votingworks/nOAuth) locally, runs it, and configures Arlo to use it. It creates the necessary audit administrator and jurisdiction administrator credentials discussed above, and launches a dev instance of Arlo. Once you have navigated to `localhost:3000` in your broswer, you should be able to log in as an audit admin using the credentials you configured earlier in the script.

#### Troubleshooting

- Postgres is best installed by grabbing `postgresql-server-dev-10` and `postgresql-client-10`.
- `psychopg2` has known issues depending on your install (see, e.g., [here](https://github.com/psycopg/psycopg2/issues/674)). If you run into issues, switch `psychopg2` to `psychopg2-binary` in the Pipfile
- `pipenv install` can hang attempting to get [a lock on the packages it's installing](https://github.com/pypa/pipenv/issues/3827). To get around this, add the `--skip-lock` flag in the Makefile (the first line should be `pipenv install --skip-lock`).
- A password may have to be set in the `DATABASE_URL` env var depending on your install of postgres. To do this, change `postgresql://postgres@localhost:5432/arlo` to `postgresql://postgres:{PASSWORD}@localhost:5432/arlo`, replacing `{PASSWORD}` with the password.
- You may need to create `arlo` and `arlo-test` databases manually [via postgres](https://www.postgresql.org/docs/9.0/sql-createdatabase.html).
- If you run into the error `fe_sendauth: no password supplied` when running
  `make dev-environment`, it means there's no password set for the default
  postgres user. You can change the postgres authentication method to not
  require a password by editing `/etc/postgresql/10/main/pg_hba.conf` and
  changing `md5` to `trust` for both the IPv4 and IPv6 local connections
  settings, and then restart postgres via `sudo systemctl restart postgresql`.

### Testing

To run the tests all the way through, use these commands:

- `make resettestdb` (to reset the testdb)
- `make test-server` or `make test-server-coverage`
- `make test-client`
- `./client/run-cypress-tests.sh`

To run tests while developing, you can use these commands to make things more interactive:

- Server tests: `pipenv run pytest` (you can add flags - e.g. `-k <pattern>` only runs tests that match the pattern, `-n auto` to run the tests in parallel)
- Client tests: `yarn --cwd client test` (runs interactive test CLI)
- End-to-end tests: first run `FLASK_ENV=test ./run-dev.sh` to run the server, then, in a separate shell, run `yarn --cwd client run cypress open` (opens the Cypress test app for interactive test running/debugging)
