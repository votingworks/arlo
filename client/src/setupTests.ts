// test-setup.js

import { dirname } from 'path'
import { afterEach, expect } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as testingLibraryMatchers from '@testing-library/jest-dom/matchers'
import 'vitest-canvas-mock'
import { comparePdfToSnapshot, CompareOptions } from 'pdf-visual-diff'
// eslint-disable-next-line import/no-extraneous-dependencies
import * as napiCanvas from '@napi-rs/canvas'

expect.extend(testingLibraryMatchers)

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace jest {
    interface Matchers<R> {
      toMatchPdfSnapshot(options?: CompareOptions): Promise<R>
    }
  }
}

expect.extend({
  async toMatchPdfSnapshot(pdf: string | Buffer, options?: CompareOptions) {
    const { isNot, testPath, currentTestName } = this
    if (isNot) {
      throw new Error(
        'Vitest: `.not` cannot be used with `.toMatchPdfSnapshot()`.'
      )
    }

    if (!testPath || !currentTestName) {
      throw new Error('Missing test path or name')
    }

    const currentDirectory = dirname(testPath)
    const snapshotName = currentTestName?.split(' ').join('_')

    // pdf-visual-diff renders PDFs via pdfjs-dist onto @napi-rs/canvas, but
    // pdfjs reads Path2D/DOMMatrix/ImageData from the global scope, where
    // vitest-canvas-mock has installed mocks that @napi-rs/canvas can't
    // consume. Swap in the real implementations for the comparison.
    const mockCanvasGlobals = {
      Path2D: window.Path2D,
      DOMMatrix: window.DOMMatrix,
      ImageData: window.ImageData,
    }
    const napiCanvasGlobals = {
      Path2D: napiCanvas.Path2D,
      DOMMatrix: napiCanvas.DOMMatrix,
      ImageData: napiCanvas.ImageData,
    }
    Object.assign(globalThis, napiCanvasGlobals)
    Object.assign(window, napiCanvasGlobals)
    try {
      const pass = await comparePdfToSnapshot(
        pdf,
        currentDirectory,
        snapshotName,
        options
      )
      return {
        pass,
        message: () => 'Does not match with snapshot.',
      }
    } finally {
      Object.assign(globalThis, mockCanvasGlobals)
      Object.assign(window, mockCanvasGlobals)
    }
  },
})

Object.defineProperty(window.document, 'createRange', {
  value: () => ({
    setStart() {
      // intentionally empty
    },
    setEnd() {
      // intentionally empty
    },
    commonAncestorContainer: {
      nodeName: 'BODY',
      ownerDocument: document,
    },
  }),
})

afterEach(cleanup)
