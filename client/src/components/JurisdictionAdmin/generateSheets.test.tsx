import React from 'react'
import { render } from '@testing-library/react'
import QRs from './QRs'
import {
  downloadAuditBoardCredentials,
  downloadPlaceholders,
  downloadLabels,
  downloadBatchTallySheets,
  downloadTallyEntryLoginLinkPrintout,
  IMinimalContest,
  downloadStackLabels,
} from './generateSheets'
import { IAuditBoard } from '../useAuditBoards'
import { jaApiCalls, auditBoardMocks } from '../_mocks'
import { dummyBallots, dummyBallotsMultipage } from '../AuditBoard/_mocks'
import { withMockFetch } from '../testUtilities'
import { roundMocks, tallyEntryAccountStatusMocks } from './_mocks'
import { IBatch } from './useBatchResults'

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

function constructMinimalContest(
  contestName: string,
  numChoices: number
): IMinimalContest {
  const choices = []
  for (let i = 0; i < numChoices; i += 1) {
    choices.push({ name: `${contestName} Candidate ${i + 1}` })
  }
  return { name: contestName, choices }
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
              imprintedId: `i-${b.position}`,
              recordId: `r-${b.position}`,
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
              imprintedId: `i-${b.position}`,
              recordId: `r-${b.position}`,
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
                imprintedId: `i-${b.position}`,
                recordId: `r-${b.position}`,
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
        [constructMinimalContest('Contest 1', 2)],
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
        [constructMinimalContest('Contest 1', 2)],
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
      const contest: IMinimalContest = {
        name: allStarLyrics,
        choices: [{ name: allStarLyrics }, { name: allStarLyrics }],
      }
      const jurisdictionName = allStarLyrics
      const pdf = await downloadBatchTallySheets(
        batches,
        [contest],
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
      const contest: IMinimalContest = {
        name: manyAs,
        choices: [{ name: manyAs }, { name: manyAs }],
      }
      const jurisdictionName = manyAs
      const pdf = await downloadBatchTallySheets(
        batches,
        [contest],
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

    it('Handles contest with many choices', async () => {
      const pdf = await downloadBatchTallySheets(
        mockBatches,
        [constructMinimalContest('Contest 1', 20)],
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

    it('Handles two contests', async () => {
      const pdf = await downloadBatchTallySheets(
        mockBatches,
        [
          constructMinimalContest('Contest 1', 2),
          constructMinimalContest('Contest 2', 2),
        ],
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

    it('Handles two contests with many choices', async () => {
      const pdf = await downloadBatchTallySheets(
        mockBatches,
        [
          constructMinimalContest('Contest 1', 20),
          constructMinimalContest('Contest 2', 20),
        ],
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

    it('Handles more than two contests', async () => {
      const pdf = await downloadBatchTallySheets(
        mockBatches,
        [
          constructMinimalContest('Contest 1', 2),
          constructMinimalContest('Contest 2', 2),
          constructMinimalContest('Contest 3', 2),
          constructMinimalContest('Contest 4', 2),
          constructMinimalContest('Contest 5', 2),
        ],
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

    // Cover all possible after-table page breaks
    for (let i = 0; i < 10; i += 1) {
      it(`Adds page break after table if necessary - ${i + 1}`, async () => {
        const pdf = await downloadBatchTallySheets(
          mockBatches,
          [constructMinimalContest('Contest 1', 5 + i)],
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

  const names = [
    'Aaron Adams',
    'Barry Batts',
    'Crazy Cabbs',
    'Danny Durnham Sr.',
    'Elliot Ezekiel III',
    'Farrih Fallahahahah ii',
    'Farrih Fallahahahahah Jr',
    'Hubert Blaine Wolfeschlegelsteinhausenbergerdorff Sr',
  ]

  describe('downloadStackLabels', () => {
    it('Generates stack labels for multiple contests', async () => {
      const pdf = await downloadStackLabels(
        mockJurisdiction.election.auditName,
        [
          constructMinimalContest('Contest 1', 4),
          constructMinimalContest('Contest 2', 4),
        ],
        mockJurisdiction.name
      )
      await expect(Buffer.from(pdf)).toMatchPdfSnapshot()
      expect(mockSavePDF).toHaveBeenCalledWith(
        `Stack Labels - ${mockJurisdiction.name} - ${mockJurisdiction.election.auditName}.pdf`,
        {
          returnPromise: true,
        }
      )
    })

    it('Generates stack labels for long names', async () => {
      const choices = []
      for (let i = 0; i < names.length; i += 1) {
        choices.push({ name: names[i] })
      }
      const contest = { name: 'Secretary of State', choices }

      const pdf = await downloadStackLabels(
        mockJurisdiction.election.auditName,
        [contest],
        mockJurisdiction.name
      )
      await expect(Buffer.from(pdf)).toMatchPdfSnapshot()
      expect(mockSavePDF).toHaveBeenCalledWith(
        `Stack Labels - ${mockJurisdiction.name} - ${mockJurisdiction.election.auditName}.pdf`,
        {
          returnPromise: true,
        }
      )
    })

    it('Generates stack labels with long contest name', async () => {
      const allStarLyrics =
        "Hey now, you're an all-star, get your game on, go play / Hey now, you're a rock star, get the show on, get paid / And all that glitters is gold / Only shooting stars break the mold"

      const pdf = await downloadStackLabels(
        mockJurisdiction.election.auditName,
        [constructMinimalContest(allStarLyrics, 8)],
        mockJurisdiction.name
      )
      await expect(Buffer.from(pdf)).toMatchPdfSnapshot()
      expect(mockSavePDF).toHaveBeenCalledWith(
        `Stack Labels - ${mockJurisdiction.name} - ${mockJurisdiction.election.auditName}.pdf`,
        {
          returnPromise: true,
        }
      )
    })
  })
})
