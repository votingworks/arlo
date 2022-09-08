// Config for stylelint parsing CSS in Styled Components
// Note the `--fix` flag doesn't yet work for CSS-in-JS
module.exports = {
  processors: ['stylelint-processor-styled-components'],
  extends: [
    'stylelint-config-palantir',
    'stylelint-config-prettier',
    'stylelint-config-styled-components',
  ],
  rules: {
    'selector-max-id': 1,
    'selector-max-universal': 1,
    'order/properties-order': null,
  },
}
