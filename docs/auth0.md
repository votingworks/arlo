# Auth0

Auth0 is used for authentication. Key things to keep in mind:

- we use Auth0 in first-party mode, meaning the same entity controls
  the Auth0 tenant and the Arlo application.

- we enable "skipping consent screen" in auth0 / APIs / Settings so
  that there isn't an OAuth consent screen, since that makes no sense
  since we're a first-party app.

- we use two separate Auth0 tenants, one for audit administrators, one
  for jurisdiction administrators, each with its own single
  application, so we can use completely different login screens for
  both, specifically 2FA for audit administrators, and both 2FA
  and passwordless for jurisdiction administrators / audit boards.

- setting up auth0 passwordless requires either creating users via the
  Management API, or letting anyone sign in and filtering on our
  end. We'll start with the latter, creating URLs for audit boards on
  the fly, but we may do the former at some point.

- right now we're using "Universal Login", where Auth0 controls the
  login page. It's not clear that's the right way forward for Arlo, as
  customization is limited and we can't unify the login flows or
  provide error messages on invalid email address at the ideal
  time. We may want the embedded login form, even though auth0
  considers that not as good an integration.
