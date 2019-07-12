// Config for stylelint parsing CSS
module.exports = {
    extends: [
      'stylelint-config-palantir',
      'stylelint-config-prettier',
    ],
    rules: {
      'selector-max-id': 1,
      'selector-max-universal': 1,
    },
  }
  