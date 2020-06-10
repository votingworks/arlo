# Release Notes

## V1

- 100% unit test coverage
- Adding and removing choices/candidates from contests
- Separate names for elections and contests
- Selecting initial sample size from among generated sample size options
- Possible number of audit boards changed from 5 to 15
- Added support for IE11
- Form validation and warnings
- Driving default form state from `/election/{electionId}/audit/status` endpoint
  to preserve progress through sessions
- Layout improvements
- Internal refactoring for efficiency and maintainability

Partial Implementation

- Adding and removing contests is supported in the frontend, but hidden until
  the backend also supports it
