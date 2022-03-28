# Auth0

Auth0 is used for authentication. Key things to keep in mind:

- we use Auth0 in first-party mode, meaning the same entity controls
  the Auth0 tenant and the Arlo application.

- we enable "skipping consent screen" in auth0 / APIs / Settings so
  that there isn't an OAuth consent screen, since that makes no sense
  since we're a first-party app.

- we use two separate Auth0 tenants, one for audit administrators, one
  for support users, each with its own single application, so we can use
  completely different login screens for both.
