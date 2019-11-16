// test-setup.js

import '@testing-library/jest-dom/extend-expect'
import '@testing-library/react/cleanup-after-each'

HTMLCanvasElement.prototype.getContext = jest.fn()
