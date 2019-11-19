# Arlo Style Guide

## [Architectural Choices for the UI](#architecture)

1. React without Redux

Keeping things simple and using minimal dependencies to reduce complexity in a
minimalist architecture. React is a lightweight and elegant front-end library
that allows us to get right to business without unnecessary overhead.

2. React Hooks and functional components

Hooks allow lightweight functional components. Hooks allow one way of working
with lifecycle methods while using functional components instead of class
components. Using 100% functional components is more performant and allows
greater convenience for maintenance.

3. Typescript

For better or for worse, Typescript helps forestall bugs and errors before they
make it to live code.

4. Server state is the single source of truth for the app state

In order to make sure that the client and the server data are in sync, and to
handle concurrency, the app state will come from the server state directly
through API calls. The `/election/{electionId}/audit/status` endpoint will be
called to update the component data on page load and also after data is sent to
the server.

5. Formik form library & Yup validation library

Using [Formik](https://github.com/jaredpalmer/formik) +
[Yup](https://github.com/jquense/yup) allows for simplified form state
management while supporting robust validation. No need to reinvent the wheel.

6. React Testing Library + Jest

[Jest](https://jestjs.io/) is the natural choice for working with React testing,
and
[React Testing Library](https://testing-library.com/docs/react-testing-library/intro)
has several advantages over Enzyme such as encouraging testing practices that
better reflect how an end user will actually use the app. Testing will focus as
much as possible on interactions from a user's perspective rather than on
implementation details. Maintaining unit test coverage of the codebase at 100%
is a priority for maintaining consistency and stability while developing.

7. Styled Components

Using [Styled Components](https://www.styled-components.com/) to keep components
more readable while maintaining sane separation of concerns.

Under Consideration

- Sharing components when possible between BMD and Arlo (https://bit.dev/ ?)

## Chosen Best Coding Practices

.. coming soon!
