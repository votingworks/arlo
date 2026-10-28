import type * as jspdf from 'jspdf'
import { Mock } from 'vitest'

/** Returns a `jspdf` module whose documents skip images and save via `mockSave`. */
const mockJsPDFModule = (
  { jsPDF }: typeof jspdf,
  mockSave: Mock
): Partial<typeof jspdf> => {
  class MockJsPDF extends jsPDF {
    override addImage(): this {
      return this
    }

    override save = mockSave
  }
  return { default: MockJsPDF, jsPDF: MockJsPDF }
}

export default mockJsPDFModule
