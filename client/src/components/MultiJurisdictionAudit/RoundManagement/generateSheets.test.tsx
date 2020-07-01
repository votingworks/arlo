import React from 'react'
import { render } from '@testing-library/react'
import { auditBoardMocks } from '../_mocks'
import QRs from './QRs'
import {
  downloadDataEntry,
  downloadPlaceholders,
  downloadLabels,
} from './generateSheets'
import { IAuditBoard } from '../useAuditBoards'
import { dummyBallots } from '../../SingleJurisdictionAudit/_mocks'

jest.mock('jspdf', () => {
  const realjspdf = jest.requireActual('jspdf')
  const mockjspdf = new realjspdf({ format: 'letter' })
  // eslint-disable-next-line func-names
  return function() {
    return {
      ...mockjspdf,
      addImage: jest.fn(),
    }
  }
})

window.URL.createObjectURL = jest.fn()

describe('generateSheets', () => {
  describe('downloadLabels', () => {
    it('generates label sheets', async () => {
      const pdf = await downloadLabels(1, dummyBallots.ballots)
      const deterministicPDF = pdf
        .replace(/CreationDate \([^)]+\)/g, '') // remove the timestamp
        .replace(/ID \[[^\]]+\]/g, '') // remove the unique id
      expect(deterministicPDF).toMatchSnapshot()
    })

    it('does nothing with no ballots', async () => {
      const pdf = await downloadLabels(1, [])
      const deterministicPDF = pdf
        .replace(/CreationDate \([^)]+\)/g, '') // remove the timestamp
        .replace(/ID \[[^\]]+\]/g, '') // remove the unique id
      expect(deterministicPDF).toMatchSnapshot()
    })
  })

  describe('downloadPlaceholders', () => {
    it('generates placeholder sheets', async () => {
      const pdf = await downloadPlaceholders(1, dummyBallots.ballots)
      const deterministicPDF = pdf
        .replace(/CreationDate \([^)]+\)/g, '') // remove the timestamp
        .replace(/ID \[[^\]]+\]/g, '') // remove the unique id
      expect(deterministicPDF).toMatchSnapshot()
    })

    it('does nothing with no ballots', async () => {
      const pdf = await downloadPlaceholders(1, [])
      const deterministicPDF = pdf
        .replace(/CreationDate \([^)]+\)/g, '') // remove the timestamp
        .replace(/ID \[[^\]]+\]/g, '') // remove the unique id
      expect(deterministicPDF).toMatchSnapshot()
    })
  })

  describe('downloadDataEntry', () => {
    it('generates data entry sheets', () => {
      render(
        <QRs
          passphrases={auditBoardMocks.double.map(
            (b: IAuditBoard) => b.passphrase
          )}
        />
      )
      const pdf = downloadDataEntry(auditBoardMocks.double)
        .replace(/CreationDate \([^)]+\)/g, '') // remove the timestamp
        .replace(/ID \[[^\]]+\]/g, '') // remove the unique id
      expect(pdf).toMatchSnapshot() // test the rest of the file now it's deterministic
    })

    it('generates data entry sheets with ballotless audit board', () => {
      window.URL.createObjectURL = jest.fn()
      render(
        <QRs
          passphrases={auditBoardMocks.noBallots.map(
            (b: IAuditBoard) => b.passphrase
          )}
        />
      )
      const pdf = downloadDataEntry(auditBoardMocks.noBallots)
        .replace(/CreationDate \([^)]+\)/g, '') // remove the timestamp
        .replace(/ID \[[^\]]+\]/g, '') // remove the unique id
      expect(pdf).toMatchSnapshot() // test the rest of the file now it's deterministic
    })
  })
})
