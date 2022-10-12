// This file sets up React's proxy in development mode.
//
// Currently, non-native Node languages (e.g. typescript) are explicitly not supported:
// https://facebook.github.io/create-react-app/docs/proxying-api-requests-in-development#configuring-the-proxy-manually
//
/* eslint-disable */
/* istanbul ignore file */
/* tslint:disable */

const proxy = require('http-proxy-middleware')
const target = 'http://localhost:3001/'

module.exports = function(app) {
  app.use(proxy('/auth/**', { target }))
  app.use(proxy('/api/**', { target }))
  app.use(proxy('/auditboard/*', { target }))
  app.use(proxy('/tallyentry/*', { target }))
}
