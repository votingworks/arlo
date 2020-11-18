// test-setup.js

import '@testing-library/jest-dom/extend-expect'
import 'jest-canvas-mock'
import 'pdf-visual-diff/lib/toMatchPdfSnapshot'

global.document.createRange = () => ({
  setStart: () => {},
  setEnd: () => {},
  commonAncestorContainer: {
    nodeName: 'BODY',
    ownerDocument: document,
  },
})
