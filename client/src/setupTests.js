// test-setup.js

import '@testing-library/jest-dom/extend-expect'
import 'jest-canvas-mock'

global.document.createRange = () => ({
  setStart: () => {},
  setEnd: () => {},
  commonAncestorContainer: {
    nodeName: 'BODY',
    ownerDocument: document,
  },
})
