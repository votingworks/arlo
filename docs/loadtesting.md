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

We're going to use a special OAuth server in the loadtest server
configuration, specifically
[nOAuth](https://github.com/votingworks/nOAuth). This lets the test
script easily log in as any user it wants to be, without endangering
production since production is obviously configured with the right
OAuth server (or we'd know immediately.)

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
