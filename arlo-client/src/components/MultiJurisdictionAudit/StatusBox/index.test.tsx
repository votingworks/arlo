import React from 'react'
import { toast } from 'react-toastify'
import {
  BrowserRouter as Router,
  // Router as RegularRouter,
  useParams,
} from 'react-router-dom'
import { render, fireEvent } from '@testing-library/react'
import { AuditAdminStatusBox, JurisdictionAdminStatusBox } from '.'
import {
  auditSettings,
  jurisdictionMocks,
  fileProcessingMocks,
  roundMocks,
  auditBoardMocks,
} from '../_mocks'
import { contestMocks } from '../Setup/Contests/_mocks'
import * as utilities from '../../utilities'

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'), // use actual for all non-hook parts
  useRouteMatch: jest.fn(),
  useParams: jest.fn(),
}))
const paramsMock = useParams as jest.Mock
paramsMock.mockReturnValue({
  electionId: '1',
  jurisdictionId: '1',
  view: 'setup',
})

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()

const toastSpy = jest.spyOn(toast, 'error').mockImplementation()

afterEach(() => {
  apiMock.mockClear()
  toastSpy.mockClear()
})

describe('StatusBox', () => {
  describe('AuditAdminStatusBox', () => {
    it('renders initial state', () => {
      const { getByText } = render(
        <Router>
          <AuditAdminStatusBox
            rounds={[]}
            jurisdictions={[]}
            contests={[]}
            auditSettings={auditSettings.blank}
          />
        </Router>
      )
      expect(getByText('Audit setup is not complete.')).toBeTruthy()
      expect(getByText('The audit has not started.')).toBeTruthy()
    })

    it('renders partial upload state', () => {
      const { getByText } = render(
        <Router>
          <AuditAdminStatusBox
            rounds={[]}
            jurisdictions={jurisdictionMocks.oneUnprocessedOneProcessed}
            contests={[]}
            auditSettings={auditSettings.blank}
          />
        </Router>
      )
      expect(getByText('Audit setup is not complete.')).toBeTruthy()
      expect(getByText('The audit has not started.')).toBeTruthy()
      expect(
        getByText('1 of 2 jurisdictions have completed file uploads.')
      ).toBeTruthy()
    })

    it('renders full uploads state', () => {
      const { getByText } = render(
        <Router>
          <AuditAdminStatusBox
            rounds={[]}
            jurisdictions={jurisdictionMocks.twoProcessed}
            contests={[]}
            auditSettings={auditSettings.blank}
          />
        </Router>
      )
      expect(getByText('Audit setup is not complete.')).toBeTruthy()
      expect(getByText('The audit has not started.')).toBeTruthy()
      expect(
        getByText('2 of 2 jurisdictions have completed file uploads.')
      ).toBeTruthy()
    })

    it('renders finished setup state', () => {
      const { getByText } = render(
        <Router>
          <AuditAdminStatusBox
            rounds={[]}
            jurisdictions={jurisdictionMocks.twoProcessed}
            contests={contestMocks.filledTargeted.contests}
            auditSettings={auditSettings.all}
          />
        </Router>
      )
      expect(getByText('Audit setup is complete.')).toBeTruthy()
      expect(getByText('The audit has not started.')).toBeTruthy()
      expect(
        getByText('2 of 2 jurisdictions have completed file uploads.')
      ).toBeTruthy()
    })

    it('renders one of two jurisdictions done round one state', () => {
      const { getByText } = render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.singleIncomplete}
            jurisdictions={jurisdictionMocks.oneComplete}
            contests={contestMocks.filledTargeted.contests}
            auditSettings={auditSettings.all}
          />
        </Router>
      )
      expect(getByText('Round 1 of the audit is in progress')).toBeTruthy()
      expect(
        getByText('1 of 2 jurisdictions have completed Round 1')
      ).toBeTruthy()
    })

    it('renders round complete, need another round state', () => {
      const { getByText } = render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.needAnother}
            jurisdictions={jurisdictionMocks.twoComplete}
            contests={contestMocks.filledTargeted.contests}
            auditSettings={auditSettings.all}
          />
        </Router>
      )
      expect(
        getByText('Round 1 of the audit is complete - another round is needed')
      ).toBeTruthy()
      expect(getByText('When you are ready, start Round 2')).toBeTruthy()
      expect(getByText('Start Round 2')).toBeTruthy()
    })

    it('creates the next round', () => {
      apiMock.mockImplementation(async () => ({
        message: 'success',
        ok: true,
      }))
      const { getByText } = render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.needAnother}
            jurisdictions={jurisdictionMocks.twoComplete}
            contests={contestMocks.filledTargeted.contests}
            auditSettings={auditSettings.all}
          />
        </Router>
      )
      fireEvent.click(getByText('Start Round 2'), { bubbles: true })
      expect(apiMock).toHaveBeenCalledTimes(1)
      expect(apiMock).toHaveBeenCalledWith('/election/1/round', {
        method: 'POST',
        body: JSON.stringify({
          roundNum: 2,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
    })

    it('handles an error when trying to create next round', () => {
      apiMock.mockImplementationOnce(() => {
        throw new Error('A test error')
      })
      const { getByText } = render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.needAnother}
            jurisdictions={jurisdictionMocks.twoComplete}
            contests={contestMocks.filledTargeted.contests}
            auditSettings={auditSettings.all}
          />
        </Router>
      )
      fireEvent.click(getByText('Start Round 2'), { bubbles: true })
      expect(apiMock).toHaveBeenCalledTimes(1)
      expect(apiMock).toHaveBeenCalledWith('/election/1/round', {
        method: 'POST',
        body: JSON.stringify({
          roundNum: 2,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      expect(toastSpy).toHaveBeenCalledTimes(1)
      expect(toastSpy).toBeCalledWith('A test error')
    })

    it('renders audit completion state', () => {
      const { getByText } = render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.singleComplete}
            jurisdictions={jurisdictionMocks.twoComplete}
            contests={contestMocks.filledTargeted.contests}
            auditSettings={auditSettings.all}
          />
        </Router>
      )
      expect(getByText('Congratulations - the audit is complete!')).toBeTruthy()
      expect(getByText('Download Audit Report')).toBeTruthy()
    })

    it('downloads audit report', () => {
      window.open = jest.fn()
      const { getByText } = render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.singleComplete}
            jurisdictions={jurisdictionMocks.twoComplete}
            contests={contestMocks.filledTargeted.contests}
            auditSettings={auditSettings.all}
          />
        </Router>
      )
      fireEvent.click(getByText('Download Audit Report'), { bubbles: true })
      expect(window.open).toHaveBeenCalledTimes(1)
      expect(window.open).toBeCalledWith(`/election/1/report`)
    })
  })

  describe('JurisdictionAdminStatusBox', () => {
    it('renders unuploaded ballot manifest initial state', () => {
      const { getByText } = render(
        <Router>
          <JurisdictionAdminStatusBox
            rounds={[]}
            auditBoards={[]}
            ballotManifest={{ file: null, processing: null }}
          />
        </Router>
      )
      expect(getByText('The audit has not started.')).toBeTruthy()
      expect(getByText('Ballot manifest not uploaded.')).toBeTruthy()
    })

    it('renders uploaded ballot manifest state', () => {
      const { getByText } = render(
        <Router>
          <JurisdictionAdminStatusBox
            rounds={[]}
            auditBoards={[]}
            ballotManifest={{
              file: null,
              processing: fileProcessingMocks.processed,
            }}
          />
        </Router>
      )
      expect(getByText('The audit has not started.')).toBeTruthy()
      expect(getByText('Ballot manifest uploaded.')).toBeTruthy()
      expect(
        getByText('Waiting for Audit Administrator to launch audit.')
      ).toBeTruthy()
    })

    it('renders 1st round in progress, has not set up audit boards state', () => {
      const { getByText } = render(
        <Router>
          <JurisdictionAdminStatusBox
            rounds={roundMocks.singleIncomplete}
            auditBoards={[]}
            ballotManifest={{
              file: null,
              processing: fileProcessingMocks.processed,
            }}
          />
        </Router>
      )
      expect(getByText('Round 1 of the audit is in progress.')).toBeTruthy()
      expect(getByText('Audit boards not set up.')).toBeTruthy()
    })

    it('renders 1st round in progress, audit boards set up, unfinished audited state', () => {
      const { getByText } = render(
        <Router>
          <JurisdictionAdminStatusBox
            rounds={roundMocks.singleIncomplete}
            auditBoards={auditBoardMocks.unfinished}
            ballotManifest={{
              file: null,
              processing: fileProcessingMocks.processed,
            }}
          />
        </Router>
      )
      expect(getByText('Round 1 of the audit is in progress.')).toBeTruthy()
      expect(getByText('0 of 1 audit boards complete.')).toBeTruthy()
    })

    it('renders 1st round finished, incomplete audit state', () => {
      const { getByText } = render(
        <Router>
          <JurisdictionAdminStatusBox
            rounds={roundMocks.singleIncomplete}
            auditBoards={auditBoardMocks.finished}
            ballotManifest={{
              file: null,
              processing: fileProcessingMocks.processed,
            }}
          />
        </Router>
      )
      expect(getByText('Round 1 of the audit is in progress.')).toBeTruthy()
      expect(getByText('1 of 1 audit boards complete.')).toBeTruthy()
      expect(
        getByText('Waiting for all jurisdictions to complete Round 1.')
      ).toBeTruthy()
    })

    it('renders completion in first round state', () => {
      const { getByText } = render(
        <Router>
          <JurisdictionAdminStatusBox
            rounds={roundMocks.singleComplete}
            auditBoards={auditBoardMocks.finished}
            ballotManifest={{
              file: null,
              processing: fileProcessingMocks.processed,
            }}
          />
        </Router>
      )
      expect(getByText('The audit is complete')).toBeTruthy()
      expect(getByText('Download the audit report.')).toBeTruthy()
      expect(getByText('Download Audit Report')).toBeTruthy()
    })

    it('downloads audit report', () => {
      window.open = jest.fn()
      const { getByText } = render(
        <Router>
          <JurisdictionAdminStatusBox
            rounds={roundMocks.singleComplete}
            auditBoards={auditBoardMocks.finished}
            ballotManifest={{
              file: null,
              processing: fileProcessingMocks.processed,
            }}
          />
        </Router>
      )
      fireEvent.click(getByText('Download Audit Report'), { bubbles: true })
      expect(window.open).toHaveBeenCalledTimes(1)
      expect(window.open).toHaveBeenCalledWith(
        '/election/1/jurisdiction/1/report'
      )
    })
  })
})
