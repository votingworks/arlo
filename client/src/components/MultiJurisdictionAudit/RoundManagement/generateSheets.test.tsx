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
import { jaApiCalls } from '../_mocks'
import { dummyBallots } from '../../DataEntry/_mocks'

const mockJurisdiction = jaApiCalls.getUser.response.user.jurisdictions[0]

const mockSavePDF = jest.fn()
jest.mock('jspdf', () => {
  const realjspdf = jest.requireActual('jspdf')
  // eslint-disable-next-line func-names, @typescript-eslint/no-explicit-any
  return function(options: any) {
    const mockjspdf = new realjspdf(options)
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
      const pdf = downloadLabels(
        1,
        dummyBallots.ballots,
        mockJurisdiction.name,
        mockJurisdiction.election.auditName
      )
      await expect(Buffer.from(pdf)).toMatchPdfSnapshot()
      expect(mockSavePDF).toHaveBeenCalledWith(
        'Round 1 Labels - Jurisdiction One - audit one.pdf'
      )
    })

    it('does nothing with no ballots', () => {
      const pdf = downloadLabels(
        1,
        [],
        mockJurisdiction.name,
        mockJurisdiction.election.auditName
      )
      expect(pdf).toEqual('')
      expect(mockSavePDF).not.toHaveBeenCalled()
    })
  })

  describe('downloadPlaceholders', () => {
    jest.setTimeout(10000)
    it('generates placeholder sheets', async () => {
      const pdf = downloadPlaceholders(
        1,
        // Test times out with too many ballots cuz the placeholder image is so large
        dummyBallots.ballots.slice(0, 5),
        mockJurisdiction.name,
        mockJurisdiction.election.auditName
      )
      await expect(Buffer.from(pdf)).toMatchPdfSnapshot()
      expect(mockSavePDF).toHaveBeenCalledWith(
        'Round 1 Placeholders - Jurisdiction One - audit one.pdf'
      )
    })

    it('generates placeholder sheets for ballot comparison audits', async () => {
      const dummyBallotComparisonBallots = dummyBallots.ballots.map(b => ({
        ...b,
        imprintedId: `${b.batch.name}-${b.position}`,
        contestsOnBallot: ['contest-id-2'],
      }))
      const pdf = downloadPlaceholders(
        1,
        // Test times out with too many ballots cuz the placeholder image is so large
        dummyBallotComparisonBallots.slice(0, 5),
        mockJurisdiction.name,
        mockJurisdiction.election.auditName
      )
      await expect(Buffer.from(pdf)).toMatchPdfSnapshot()
      expect(mockSavePDF).toHaveBeenCalledWith(
        'Round 1 Placeholders - Jurisdiction One - audit one.pdf'
      )
    })

    it('does nothing with no ballots', () => {
      const pdf = downloadPlaceholders(
        1,
        [],
        mockJurisdiction.name,
        mockJurisdiction.election.auditName
      )
      expect(pdf).toEqual('')
      expect(mockSavePDF).not.toHaveBeenCalled()
    })
  })

  describe('downloadAuditBoardCredentials', () => {
    it('generates audit board credentials sheets', async () => {
      render(
        <QRs
          passphrases={auditBoardMocks.double.map(
            (b: IAuditBoard) => b.passphrase
          )}
        />
      )
      const pdf = downloadAuditBoardCredentials(
        auditBoardMocks.double,
        mockJurisdiction.name,
        mockJurisdiction.election.auditName
      )
      await expect(Buffer.from(pdf)).toMatchPdfSnapshot()
      expect(mockSavePDF).toHaveBeenCalledWith(
        'Audit Board Credentials - Jurisdiction One - audit one.pdf'
      )
    })

    it('generates audit board credentials sheets with ballotless audit board', async () => {
      render(
        <QRs
          passphrases={auditBoardMocks.noBallots.map(
            (b: IAuditBoard) => b.passphrase
          )}
        />
      )
      const pdf = downloadAuditBoardCredentials(
        auditBoardMocks.noBallots,
        mockJurisdiction.name,
        mockJurisdiction.election.auditName
      )
      await expect(Buffer.from(pdf)).toMatchPdfSnapshot()
      expect(mockSavePDF).toHaveBeenCalledWith(
        'Audit Board Credentials - Jurisdiction One - audit one.pdf'
      )
    })
  })
})
