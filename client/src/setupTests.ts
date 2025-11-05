// test-setup.js

import { dirname } from 'path'
import { afterEach, expect } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as testingLibraryMatchers from '@testing-library/jest-dom/matchers'
import 'vitest-canvas-mock'
import 'pdf-visual-diff'
import { comparePdfToSnapshot } from 'pdf-visual-diff/lib/compare-pdf-to-snapshot'
import { CompareImagesOpts } from 'pdf-visual-diff/lib/compare-images'
import { CompareOptions } from 'pdf-visual-diff/lib/compare'

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

    const pass = await comparePdfToSnapshot(
      pdf,
      currentDirectory,
      snapshotName,
      options as Partial<CompareImagesOpts>
    )
    return {
      pass,
      message: () => 'Does not match with snapshot.',
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
