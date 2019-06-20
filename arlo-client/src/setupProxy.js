// This file sets up React's proxy in development mode.
//
// Currently, non-native Node languages (e.g. typescript) are explicitly not supported:
// https://facebook.github.io/create-react-app/docs/proxying-api-requests-in-development#configuring-the-proxy-manually
//
/* eslint-disable */
/* istanbul ignore file */

const proxy = require('http-proxy-middleware')

module.exports = function(app) {
  app.use(proxy('/admin', { target: 'http://localhost:3001/' }))
  app.use(proxy('/audit', { target: 'http://localhost:3001/' }))
}
