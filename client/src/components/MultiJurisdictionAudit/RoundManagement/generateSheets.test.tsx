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
import { dummyBallots, dummyBallotsMultipage } from '../../DataEntry/_mocks'
import { withMockFetch } from '../../testUtilities'
import { roundMocks } from './_mocks'

const mockJurisdiction = jaApiCalls.getUser.response.user.jurisdictions[0]
const mockRound = roundMocks.incomplete

const mockSavePDF = jest.fn()
jest.mock('jspdf', () => {
  const { jsPDF } = jest.requireActual('jspdf')
  // eslint-disable-next-line func-names, @typescript-eslint/no-explicit-any
  return function(options: any) {
    const mockjspdf = new jsPDF(options)
    return {
      ...mockjspdf,
      addImage: jest.fn(),
      save: mockSavePDF,
    }
  }
})

window.URL.createObjectURL = jest.fn()

const apiCalls = {
  getBallots: {
    url: `/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/ballots`,
    response: dummyBallots,
  },
  getBallotsMultipage: {
    url: `/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/ballots`,
    response: dummyBallotsMultipage,
  },
}

describe('generateSheets', () => {
  beforeEach(() => mockSavePDF.mockClear())

  describe('downloadLabels', () => {
    it('generates label sheets', async () => {
      const expectedCalls = [apiCalls.getBallots]
      await withMockFetch(expectedCalls, async () => {
        const pdf = await downloadLabels(
          mockJurisdiction.election.id,
          mockJurisdiction.id,
          mockRound,
          mockJurisdiction.name,
          mockJurisdiction.election.auditName
        )
        await expect(Buffer.from(pdf)).toMatchPdfSnapshot()
        expect(mockSavePDF).toHaveBeenCalledWith(
          'Round 1 Labels - Jurisdiction One - audit one.pdf',
          { returnPromise: true }
        )
      })
    })

    it('generates multiple pages of sheets & wrap long lines', async () => {
      const expectedCalls = [apiCalls.getBallotsMultipage]
      await withMockFetch(expectedCalls, async () => {
        const pdf = await downloadLabels(
          mockJurisdiction.election.id,
          mockJurisdiction.id,
          mockRound,
          mockJurisdiction.name,
          mockJurisdiction.election.auditName
        )
        await expect(Buffer.from(pdf)).toMatchPdfSnapshot()
        expect(mockSavePDF).toHaveBeenCalledWith(
          'Round 1 Labels - Jurisdiction One - audit one.pdf',
          { returnPromise: true }
        )
      })
    })

    it('generates label sheets for ballot comparison audits', async () => {
      const expectedCalls = [
        {
          ...apiCalls.getBallots,
          response: {
            ballots: dummyBallots.ballots.map(b => ({
              ...b,
              imprintedId: `${b.batch.name}-${b.position}`,
            })),
          },
        },
      ]
      await withMockFetch(expectedCalls, async () => {
        const pdf = await downloadLabels(
          mockJurisdiction.election.id,
          mockJurisdiction.id,
          mockRound,
          mockJurisdiction.name,
          mockJurisdiction.election.auditName
        )
        await expect(Buffer.from(pdf)).toMatchPdfSnapshot()
        expect(mockSavePDF).toHaveBeenCalledWith(
          'Round 1 Labels - Jurisdiction One - audit one.pdf',
          { returnPromise: true }
        )
      })
    })

    it('check for long lines for ballot comparison audits', async () => {
      const expectedCalls = [
        {
          ...apiCalls.getBallots,
          response: {
            ballots: dummyBallots.ballots.map(b => ({
              ...b,
              imprintedId: `${b.batch.name}-${b.position}`,
              batch: {
                ...b.batch,
                container: '5',
              },
            })),
          },
        },
      ]
      await withMockFetch(expectedCalls, async () => {
        const pdf = await downloadLabels(
          mockJurisdiction.election.id,
          mockJurisdiction.id,
          mockRound,
          mockJurisdiction.name,
          mockJurisdiction.election.auditName
        )
        await expect(Buffer.from(pdf)).toMatchPdfSnapshot()
        expect(mockSavePDF).toHaveBeenCalledWith(
          'Round 1 Labels - Jurisdiction One - audit one.pdf',
          { returnPromise: true }
        )
      })
    })

    it('does nothing with no ballots', async () => {
      const expectedCalls = [
        { ...apiCalls.getBallots, response: { ballots: [] } },
      ]
      await withMockFetch(expectedCalls, async () => {
        const pdf = await downloadLabels(
          mockJurisdiction.election.id,
          mockJurisdiction.id,
          mockRound,
          mockJurisdiction.name,
          mockJurisdiction.election.auditName
        )
        expect(pdf).toEqual('')
        expect(mockSavePDF).not.toHaveBeenCalled()
      })
    })
  })

  describe('downloadPlaceholders', () => {
    jest.setTimeout(10000)
    it('generates placeholder sheets', async () => {
      const expectedCalls = [
        {
          ...apiCalls.getBallots,
          // Test times out with too many ballots cuz the placeholder image is so large
          response: { ballots: dummyBallots.ballots.slice(0, 5) },
        },
      ]
      await withMockFetch(expectedCalls, async () => {
        const pdf = await downloadPlaceholders(
          mockJurisdiction.election.id,
          mockJurisdiction.id,
          mockRound,
          mockJurisdiction.name,
          mockJurisdiction.election.auditName
        )
        await expect(Buffer.from(pdf)).toMatchPdfSnapshot()
        expect(mockSavePDF).toHaveBeenCalledWith(
          'Round 1 Placeholders - Jurisdiction One - audit one.pdf',
          { returnPromise: true }
        )
      })
    })

    it('generates placeholder sheets for ballot comparison audits', async () => {
      const expectedCalls = [
        {
          ...apiCalls.getBallots,
          // Test times out with too many ballots cuz the placeholder image is so large
          response: {
            ballots: dummyBallots.ballots
              .map(b => ({
                ...b,
                imprintedId: `${b.batch.name}-${b.position}`,
              }))
              .slice(0, 5),
          },
        },
      ]
      await withMockFetch(expectedCalls, async () => {
        const pdf = await downloadPlaceholders(
          mockJurisdiction.election.id,
          mockJurisdiction.id,
          mockRound,
          mockJurisdiction.name,
          mockJurisdiction.election.auditName
        )
        await expect(Buffer.from(pdf)).toMatchPdfSnapshot()
        expect(mockSavePDF).toHaveBeenCalledWith(
          'Round 1 Placeholders - Jurisdiction One - audit one.pdf',
          { returnPromise: true }
        )
      })
    })

    it('does nothing with no ballots', async () => {
      const expectedCalls = [
        { ...apiCalls.getBallots, response: { ballots: [] } },
      ]
      await withMockFetch(expectedCalls, async () => {
        const pdf = await downloadPlaceholders(
          mockJurisdiction.election.id,
          mockJurisdiction.id,
          mockRound,
          mockJurisdiction.name,
          mockJurisdiction.election.auditName
        )
        expect(pdf).toEqual('')
        expect(mockSavePDF).not.toHaveBeenCalled()
      })
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
      const pdf = await downloadAuditBoardCredentials(
        auditBoardMocks.double,
        mockJurisdiction.name,
        mockJurisdiction.election.auditName
      )
      await expect(Buffer.from(pdf)).toMatchPdfSnapshot()
      expect(mockSavePDF).toHaveBeenCalledWith(
        'Audit Board Credentials - Jurisdiction One - audit one.pdf',
        { returnPromise: true }
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
      const pdf = await downloadAuditBoardCredentials(
        auditBoardMocks.noBallots,
        mockJurisdiction.name,
        mockJurisdiction.election.auditName
      )
      await expect(Buffer.from(pdf)).toMatchPdfSnapshot()
      expect(mockSavePDF).toHaveBeenCalledWith(
        'Audit Board Credentials - Jurisdiction One - audit one.pdf',
        { returnPromise: true }
      )
    })
  })
})
