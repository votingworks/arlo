# Load Testing

We want to observe how the server behaves under realistic load. To
keep things realistic, our approach should:

- use real HTTPS requests against a load-testing system configured similarly to the real system
- use requests that look as much as possible like the real thing, e.g. with expected cookies
- figure out how to load test Arlo without also load-testing Auth0 for authentication
- whatever hacks we put in for authentication (it should be clear by
  now we'll need some), they should not affect production code.
- scale up well with ideally minimal infrastructural investment so
  we're not manually spinning up dozens of machines ourselves.

## Authentication Hack for Load Testing

We have superadmin features that allow for impersonation of any user,
and which uses the same cookies as normal logins. Let's reuse that.

We'll build a superadmin bypass using a special HTTP header. Because
we don't ever want that code in production, we'll keep that code in a
special branch, `loadtesting`, that we'll need to rebase every so
often on `master`. We'll also require that `FLASK_ENV=loadtest` as an
extra defense-in-depth measure, just in case we mistakenly merge that
branch into `master`. Belt _and_ suspenders. Reuse of `FLASK_ENV`
makes it unlikely that this environment variable would be changed to
`loadtest` in a production setting.

Finally, as an extra safeguard to prevent merging the `loadtesting`
branch, we'll fail CI with `exit 1`.

## Tool

One tool that some of us have used with success is
[Artillery](https://artillery.io), and in particular [Serverless
Artillery](https://github.com/Nordstrom/serverless-artillery), which
combines the same test scripting language with AWS Lambda deployment
for instant scaling without overhead of setting up machines.

## User Modeling

For a first test, we'll model one audit admin and 1,000 jurisdiction
administrators, with the jurisdiction administrators arriving in a
random fashion over the course of an hour to upload their manifests.

As a second test, we'll model 1,000 jurisdiction administrators going
through the ballot entry UI and completing the first stage of an
audit, over the course of 2 hours.
