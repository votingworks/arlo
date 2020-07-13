import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { useParams } from 'react-router-dom'
import RoundManagement from './index'
import { roundMocks, auditBoardMocks } from '../_mocks'
import { dummyBallots } from '../../SingleJurisdictionAudit/_mocks'
import { withMockFetch } from '../../testUtilities'
import {
  downloadPlaceholders,
  downloadLabels,
  downloadDataEntry,
} from './generateSheets'

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'), // use actual for all non-hook parts
  useRouteMatch: jest.fn(),
  useParams: jest.fn(),
}))
const paramsMock = useParams as jest.Mock
paramsMock.mockReturnValue({
  electionId: '1',
  jurisdictionId: '1',
})

jest.mock('./generateSheets', () => ({
  downloadPlaceholders: jest.fn(),
  downloadLabels: jest.fn(),
  downloadDataEntry: jest.fn(),
}))
const downloadPlaceholdersMock = downloadPlaceholders as jest.Mock
const downloadLabelsMock = downloadLabels as jest.Mock
const downloadDataEntryMock = downloadDataEntry as jest.Mock

window.open = jest.fn()

const apiCalls = {
  getBallots: {
    url: '/api/election/1/jurisdiction/1/round/round-1/ballots',
    response: dummyBallots,
  },
}

describe('RoundManagement', () => {
  it('renders initial state', async () => {
    const expectedCalls = [apiCalls.getBallots]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(
        <RoundManagement
          round={roundMocks.singleIncomplete[0]}
          auditBoards={auditBoardMocks.empty}
          createAuditBoards={jest.fn()}
        />
      )
      await screen.findByText('Round 1 Audit Board Setup')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders completed state', async () => {
    const expectedCalls = [apiCalls.getBallots]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(
        <RoundManagement
          round={roundMocks.singleComplete[0]}
          auditBoards={auditBoardMocks.empty}
          createAuditBoards={jest.fn()}
        />
      )
      await screen.findByText(
        'Congratulations! Your Risk-Limiting Audit is now complete.'
      )
      expect(container).toMatchSnapshot()
    })
  })

  it('calls pdf generation functions', async () => {
    const expectedCalls = [apiCalls.getBallots]
    await withMockFetch(expectedCalls, async () => {
      render(
        <RoundManagement
          round={roundMocks.singleIncomplete[0]}
          auditBoards={auditBoardMocks.unfinished}
          createAuditBoards={jest.fn()}
        />
      )
      fireEvent.click(
        await screen.findByText(
          'Download Aggregated Ballot Retrival List for Round 1'
        ),
        { bubbles: true }
      )
      fireEvent.click(
        await screen.findByText(
          'Download Audit Board Credentials for Data Entry'
        ),
        { bubbles: true }
      )
      fireEvent.click(
        await screen.findByText('Download Placeholder Sheets for Round 1'),
        { bubbles: true }
      )
      fireEvent.click(
        await screen.findByText('Download Ballot Labels for Round 1'),
        { bubbles: true }
      )
      expect(window.open).toHaveBeenCalledWith(
        '/api/election/1/jurisdiction/1/round/round-1/retrieval-list'
      )
      expect(downloadPlaceholdersMock).toHaveBeenCalled()
      expect(downloadLabelsMock).toHaveBeenCalled()
      expect(downloadDataEntryMock).toHaveBeenCalled()
    })
  })
})
