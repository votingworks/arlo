// This file sets up React's proxy in development mode.
//
// Currently, non-native Node languages (e.g. typescript) are explicitly not supported:
// https://facebook.github.io/create-react-app/docs/proxying-api-requests-in-development#configuring-the-proxy-manually
//
/* eslint-disable */
/* istanbul ignore file */
/* tslint:disable */

const proxy = require('http-proxy-middleware')

module.exports = function(app) {
  app.use(proxy('/election/new', { target: 'http://localhost:3001/' }))
  app.use(proxy('/election/*/audit/**', { target: 'http://localhost:3001/' }))
  app.use(proxy('/election/*/jurisdiction/**', { target: 'http://localhost:3001/' }))
  app.use(proxy('/election/*/admin/**', { target: 'http://localhost:3001/' }))
}
