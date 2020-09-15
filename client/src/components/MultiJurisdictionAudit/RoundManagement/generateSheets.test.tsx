import React from 'react'
import { render } from '@testing-library/react'
import { auditBoardMocks } from '../useSetupMenuItems/_mocks'
import QRs from './QRs'
import {
  downloadAuditBoardCredentials,
  downloadPlaceholders,
  downloadLabels,
} from './generateSheets'
import { IAuditBoard } from '../useAuditBoards'
import { dummyBallots } from '../../SingleJurisdictionAudit/_mocks'
import { jaApiCalls } from '../_mocks'

const mockJurisdiction = jaApiCalls.getUser.response.jurisdictions[0]

const mockSavePDF = jest.fn()
jest.mock('jspdf', () => {
  const realjspdf = jest.requireActual('jspdf')
  const mockjspdf = new realjspdf({ format: 'letter' })
  // eslint-disable-next-line func-names
  return function() {
    return {
      ...mockjspdf,
      addImage: jest.fn(),
      save: mockSavePDF,
    }
  }
})

window.URL.createObjectURL = jest.fn()

describe('generateSheets', () => {
  beforeEach(() => mockSavePDF.mockClear())

  describe('downloadLabels', () => {
    it('generates label sheets', async () => {
      const pdf = await downloadLabels(
        1,
        dummyBallots.ballots,
        mockJurisdiction
      )
      const deterministicPDF = pdf
        .replace(/CreationDate \([^)]+\)/g, '') // remove the timestamp
        .replace(/ID \[[^\]]+\]/g, '') // remove the unique id
      expect(deterministicPDF).toMatchSnapshot()
      expect(mockSavePDF).toHaveBeenCalledWith(
        'Round 1 Labels - Jurisdiction One - audit one.pdf'
      )
    })

    it('does nothing with no ballots', async () => {
      const pdf = await downloadLabels(1, [], mockJurisdiction)
      const deterministicPDF = pdf
        .replace(/CreationDate \([^)]+\)/g, '') // remove the timestamp
        .replace(/ID \[[^\]]+\]/g, '') // remove the unique id
      expect(deterministicPDF).toMatchSnapshot()
    })
  })

  describe('downloadPlaceholders', () => {
    it('generates placeholder sheets', async () => {
      const pdf = await downloadPlaceholders(
        1,
        dummyBallots.ballots,
        mockJurisdiction
      )
      const deterministicPDF = pdf
        .replace(/CreationDate \([^)]+\)/g, '') // remove the timestamp
        .replace(/ID \[[^\]]+\]/g, '') // remove the unique id
      expect(deterministicPDF).toMatchSnapshot()
      expect(mockSavePDF).toHaveBeenCalledWith(
        'Round 1 Placeholders - Jurisdiction One - audit one.pdf'
      )
    })

    it('does nothing with no ballots', async () => {
      const pdf = await downloadPlaceholders(1, [], mockJurisdiction)
      const deterministicPDF = pdf
        .replace(/CreationDate \([^)]+\)/g, '') // remove the timestamp
        .replace(/ID \[[^\]]+\]/g, '') // remove the unique id
      expect(deterministicPDF).toMatchSnapshot()
    })
  })

  describe('downloadAuditBoardCredentials', () => {
    it('generates audit board credentials sheets', () => {
      render(
        <QRs
          passphrases={auditBoardMocks.double.map(
            (b: IAuditBoard) => b.passphrase
          )}
        />
      )
      const pdf = downloadAuditBoardCredentials(
        auditBoardMocks.double,
        mockJurisdiction
      )
        .replace(/CreationDate \([^)]+\)/g, '') // remove the timestamp
        .replace(/ID \[[^\]]+\]/g, '') // remove the unique id
      expect(pdf).toMatchSnapshot() // test the rest of the file now it's deterministic
      expect(mockSavePDF).toHaveBeenCalledWith(
        'Audit Board Credentials - Jurisdiction One - audit one.pdf'
      )
    })

    it('generates audit board credentials sheets with ballotless audit board', () => {
      render(
        <QRs
          passphrases={auditBoardMocks.noBallots.map(
            (b: IAuditBoard) => b.passphrase
          )}
        />
      )
      const pdf = downloadAuditBoardCredentials(
        auditBoardMocks.noBallots,
        mockJurisdiction
      )
        .replace(/CreationDate \([^)]+\)/g, '') // remove the timestamp
        .replace(/ID \[[^\]]+\]/g, '') // remove the unique id
      expect(pdf).toMatchSnapshot() // test the rest of the file now it's deterministic
    })
  })
})
