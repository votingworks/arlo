import React from 'react'
import { render } from '@testing-library/react'
import { auditBoardMocks } from '../_mocks'
import QRs from './QRs'
import { downloadDataEntry } from './generateSheets'
import { IAuditBoard } from '../useAuditBoards'

describe('generateSheets', () => {
  it('generates data entry sheets', () => {
    window.URL.createObjectURL = jest.fn()
    render(
      <QRs
        passphrases={auditBoardMocks.double.map(
          (b: IAuditBoard) => b.passphrase
        )}
      />
    )
    const pdf = downloadDataEntry(auditBoardMocks.double)
    expect(pdf).toMatchSnapshot()
  })
})
