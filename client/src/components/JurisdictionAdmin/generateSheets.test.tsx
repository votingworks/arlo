import React from 'react'
import { render } from '@testing-library/react'
import QRs from './QRs'
import {
  downloadAuditBoardCredentials,
  downloadPlaceholders,
  downloadLabels,
  downloadBatchTallySheets,
  downloadTallyEntryLoginLinkPrintout,
} from './generateSheets'
import { IAuditBoard } from '../useAuditBoards'
import { jaApiCalls } from '../_mocks'
import { auditBoardMocks } from '../AuditAdmin/useSetupMenuItems/_mocks'
import { dummyBallots, dummyBallotsMultipage } from '../AuditBoard/_mocks'
import { withMockFetch } from '../testUtilities'
import { roundMocks, tallyEntryAccountStatusMocks } from './_mocks'
import { IBatch } from './useBatchResults'
import { ICandidate } from '../../types'

const mockJurisdiction = jaApiCalls.getUser.response.user.jurisdictions[0]
const mockRound = roundMocks.incomplete
const mockBatches: IBatch[] = [
  {
    id: 'B1',
    lastEditedBy: null,
    name: 'Batch #1',
    numBallots: 0,
    resultTallySheets: [],
  },
  {
    id: 'B2',
    lastEditedBy: null,
    name: 'Batch #2',
    numBallots: 0,
    resultTallySheets: [],
  },
]

function constructContestChoices(numChoices: number): ICandidate[] {
  const choices = []
  for (let i = 0; i < numChoices; i += 1) {
    choices.push({ id: `C${i + 1}`, name: `Candidate #${i + 1}`, numVotes: 0 })
  }
  return choices
}

const mockSavePDF = jest.fn()
jest.mock('jspdf', () => {
  const { jsPDF } = jest.requireActual('jspdf')
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return function mockJsPDF(options?: any) {
    return {
      ...new jsPDF(options),
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
        expect(
          mockSavePDF
        ).toHaveBeenCalledWith(
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
        expect(
          mockSavePDF
        ).toHaveBeenCalledWith(
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
        expect(
          mockSavePDF
        ).toHaveBeenCalledWith(
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
        expect(
          mockSavePDF
        ).toHaveBeenCalledWith(
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
        expect(
          mockSavePDF
        ).toHaveBeenCalledWith(
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
        expect(
          mockSavePDF
        ).toHaveBeenCalledWith(
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
      expect(
        mockSavePDF
      ).toHaveBeenCalledWith(
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
      expect(
        mockSavePDF
      ).toHaveBeenCalledWith(
        'Audit Board Credentials - Jurisdiction One - audit one.pdf',
        { returnPromise: true }
      )
    })
  })

  describe('downloadBatchTallySheets', () => {
    // Snapshots generated by a Mac Ubuntu VM can differ ever so slightly from those generated
    // by CircleCI in a way that isn't visually perceptible, so we tolerate a 0.1% diff
    // TODO: Get to the root cause of the diffs
    const diffTolerance = 0.001
    it('Generates batch tally sheets', async () => {
      const pdf = await downloadBatchTallySheets(
        mockBatches,
        constructContestChoices(2),
        mockJurisdiction.name,
        mockJurisdiction.election.auditName
      )
      await expect(Buffer.from(pdf)).toMatchPdfSnapshot({
        tolerance: diffTolerance,
      })
      expect(mockSavePDF).toHaveBeenCalledWith(
        'Batch Tally Sheets - Jurisdiction One - audit one.pdf',
        {
          returnPromise: true,
        }
      )
    })

    it('Handles single-batch case', async () => {
      const pdf = await downloadBatchTallySheets(
        [mockBatches[0]],
        constructContestChoices(2),
        mockJurisdiction.name,
        mockJurisdiction.election.auditName
      )
      await expect(Buffer.from(pdf)).toMatchPdfSnapshot({
        tolerance: diffTolerance,
      })
      expect(mockSavePDF).toHaveBeenCalledWith(
        'Batch Tally Sheets - Jurisdiction One - audit one.pdf',
        {
          returnPromise: true,
        }
      )
    })

    it('Handles long content', async () => {
      const allStarLyrics =
        "Hey now, you're an all-star, get your game on, go play / Hey now, you're a rock star, get the show on, get paid / And all that glitters is gold / Only shooting stars break the mold"
      const batches: IBatch[] = [
        {
          id: 'B1',
          lastEditedBy: null,
          name: allStarLyrics,
          numBallots: 0,
          resultTallySheets: [],
        },
        {
          id: 'B2',
          lastEditedBy: null,
          name: allStarLyrics,
          numBallots: 0,
          resultTallySheets: [],
        },
      ]
      const contestChoices: ICandidate[] = [
        { id: 'C1', name: allStarLyrics, numVotes: 0 },
        { id: 'C2', name: allStarLyrics, numVotes: 0 },
        { id: 'C3', name: allStarLyrics, numVotes: 0 },
        { id: 'C4', name: allStarLyrics, numVotes: 0 },
        { id: 'C5', name: allStarLyrics, numVotes: 0 },
        { id: 'C6', name: allStarLyrics, numVotes: 0 },
      ]
      const jurisdictionName = allStarLyrics
      const pdf = await downloadBatchTallySheets(
        batches,
        contestChoices,
        jurisdictionName,
        'Test Audit'
      )
      await expect(Buffer.from(pdf)).toMatchPdfSnapshot({
        tolerance: diffTolerance,
      })
      expect(mockSavePDF).toHaveBeenCalledWith(
        `Batch Tally Sheets - ${jurisdictionName} - Test Audit.pdf`,
        {
          returnPromise: true,
        }
      )
    })

    it('Handles long content with no spaces', async () => {
      const manyAs =
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
      const batches: IBatch[] = [
        {
          id: 'B1',
          lastEditedBy: null,
          name: manyAs,
          numBallots: 0,
          resultTallySheets: [],
        },
        {
          id: 'B2',
          lastEditedBy: null,
          name: manyAs,
          numBallots: 0,
          resultTallySheets: [],
        },
      ]
      const contestChoices: ICandidate[] = [
        { id: 'C1', name: manyAs, numVotes: 0 },
        { id: 'C2', name: manyAs, numVotes: 0 },
      ]
      const jurisdictionName = manyAs
      const pdf = await downloadBatchTallySheets(
        batches,
        contestChoices,
        jurisdictionName,
        'Test Audit'
      )
      await expect(Buffer.from(pdf)).toMatchPdfSnapshot({
        tolerance: diffTolerance,
      })
      expect(mockSavePDF).toHaveBeenCalledWith(
        `Batch Tally Sheets - ${jurisdictionName} - Test Audit.pdf`,
        {
          returnPromise: true,
        }
      )
    })

    // Cover all possible after-table page breaks
    for (let i = 0; i < 10; i += 1) {
      it(`Adds page break after table if necessary - ${i + 1}`, async () => {
        const pdf = await downloadBatchTallySheets(
          mockBatches,
          constructContestChoices(6 + i),
          mockJurisdiction.name,
          mockJurisdiction.election.auditName
        )
        await expect(Buffer.from(pdf)).toMatchPdfSnapshot({
          tolerance: diffTolerance,
        })
      })
    }
  })

  describe('downloadTallyEntryLoginLinkPrintout', () => {
    it('generates tally entry login link printout', async () => {
      const loginLinkUrl = `http://localhost/tallyentry/${tallyEntryAccountStatusMocks.noLoginRequests.passphrase}`
      const pdf = await downloadTallyEntryLoginLinkPrintout(
        loginLinkUrl,
        mockJurisdiction.name,
        mockJurisdiction.election.auditName
      )
      await expect(Buffer.from(pdf)).toMatchPdfSnapshot()
      expect(
        mockSavePDF
      ).toHaveBeenCalledWith(
        'Tally Entry Login Link - Jurisdiction One - audit one.pdf',
        { returnPromise: true }
      )
    })
  })
})
