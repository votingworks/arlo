import React from 'react'
import { BrowserRouter as Router, useParams } from 'react-router-dom'
import { render, fireEvent, screen } from '@testing-library/react'
import { AuditAdminStatusBox, JurisdictionAdminStatusBox } from '.'
import {
  auditSettings,
  jurisdictionMocks,
  fileProcessingMocks,
  roundMocks,
  auditBoardMocks,
} from '../useSetupMenuItems/_mocks'
import { contestMocks } from '../AASetup/Contests/_mocks'
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

afterEach(() => {
  apiMock.mockClear()
})

describe('StatusBox', () => {
  describe('AuditAdminStatusBox', () => {
    it('renders initial state', () => {
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={[]}
            jurisdictions={[]}
            contests={[]}
            auditSettings={auditSettings.blank!}
          />
        </Router>
      )
      screen.getByText('Audit setup is not complete.')
      screen.getByText('The audit has not started.')
    })

    it('renders partial upload state', () => {
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={[]}
            jurisdictions={jurisdictionMocks.oneManifest}
            contests={[]}
            auditSettings={auditSettings.blank!}
          />
        </Router>
      )
      screen.getByText('Audit setup is not complete.')
      screen.getByText('The audit has not started.')
      screen.getByText('1 of 3 jurisdictions have completed file uploads.')
    })

    it('renders full uploads state', () => {
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={[]}
            jurisdictions={jurisdictionMocks.allManifests}
            contests={[]}
            auditSettings={auditSettings.blank!}
          />
        </Router>
      )
      screen.getByText('Audit setup is not complete.')
      screen.getByText('The audit has not started.')
      screen.getByText('3 of 3 jurisdictions have completed file uploads.')
    })

    it('renders finished setup state', () => {
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={[]}
            jurisdictions={jurisdictionMocks.allManifests}
            contests={contestMocks.filledTargeted.contests}
            auditSettings={auditSettings.all}
          />
        </Router>
      )
      screen.getByText('Audit setup is complete.')
      screen.getByText('The audit has not started.')
      screen.getByText('3 of 3 jurisdictions have completed file uploads.')
    })

    it('renders one of two jurisdictions done round one state', () => {
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.singleIncomplete}
            jurisdictions={jurisdictionMocks.oneComplete}
            contests={contestMocks.filledTargeted.contests}
            auditSettings={auditSettings.all}
          />
        </Router>
      )
      screen.getByText('Round 1 of the audit is in progress')
      screen.getByText('1 of 3 jurisdictions have completed Round 1')
    })

    it('renders round complete, need another round state', () => {
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.needAnother}
            jurisdictions={jurisdictionMocks.allComplete}
            contests={contestMocks.filledTargeted.contests}
            auditSettings={auditSettings.all}
          />
        </Router>
      )
      screen.getByText(
        'Round 1 of the audit is complete - another round is needed'
      )
      screen.getByText('When you are ready, start Round 2')
      screen.getByText('Start Round 2')
    })

    it('creates the next round', () => {
      apiMock.mockResolvedValue({ status: 'ok' })
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.needAnother}
            jurisdictions={jurisdictionMocks.allComplete}
            contests={contestMocks.filledTargeted.contests}
            auditSettings={auditSettings.all}
          />
        </Router>
      )
      fireEvent.click(screen.getByRole('button', { name: 'Start Round 2' }), {
        bubbles: true,
      })
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
      apiMock.mockResolvedValueOnce(null)
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.needAnother}
            jurisdictions={jurisdictionMocks.allComplete}
            contests={contestMocks.filledTargeted.contests}
            auditSettings={auditSettings.all}
          />
        </Router>
      )
      fireEvent.click(screen.getByRole('button', { name: 'Start Round 2' }), {
        bubbles: true,
      })
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

    it('renders audit completion state', () => {
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.singleComplete}
            jurisdictions={jurisdictionMocks.allComplete}
            contests={contestMocks.filledTargeted.contests}
            auditSettings={auditSettings.all}
          />
        </Router>
      )
      screen.getByText('Congratulations - the audit is complete!')
      screen.getByText('Download Audit Report')
    })

    it('downloads audit report', () => {
      window.open = jest.fn()
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.singleComplete}
            jurisdictions={jurisdictionMocks.allComplete}
            contests={contestMocks.filledTargeted.contests}
            auditSettings={auditSettings.all}
          />
        </Router>
      )
      fireEvent.click(
        screen.getByRole('button', { name: 'Download Audit Report' }),
        {
          bubbles: true,
        }
      )
      expect(window.open).toHaveBeenCalledTimes(1)
      expect(window.open).toBeCalledWith(`/api/election/1/report`)
    })
  })

  describe('JurisdictionAdminStatusBox', () => {
    it('renders unuploaded ballot manifest initial state', () => {
      render(
        <Router>
          <JurisdictionAdminStatusBox
            rounds={[]}
            auditBoards={[]}
            ballotManifest={{ file: null, processing: null }}
            batchTallies={{ file: null, processing: null }}
            cvrs={{ file: null, processing: null }}
            auditType="BALLOT_POLLING"
          />
        </Router>
      )
      screen.getByText('The audit has not started.')
      screen.getByText('Ballot manifest not uploaded.')
    })

    it('renders uploaded ballot manifest state', () => {
      render(
        <Router>
          <JurisdictionAdminStatusBox
            rounds={[]}
            auditBoards={[]}
            ballotManifest={{
              file: null,
              processing: fileProcessingMocks.processed,
            }}
            batchTallies={{ file: null, processing: null }}
            cvrs={{ file: null, processing: null }}
            auditType="BALLOT_POLLING"
          />
        </Router>
      )
      screen.getByText('The audit has not started.')
      screen.getByText('Ballot manifest successfully uploaded.')
      screen.getByText('Waiting for Audit Administrator to launch audit.')
    })

    it('renders 1st round in progress, has not set up audit boards state', () => {
      render(
        <Router>
          <JurisdictionAdminStatusBox
            rounds={roundMocks.singleIncomplete}
            auditBoards={[]}
            ballotManifest={{
              file: null,
              processing: fileProcessingMocks.processed,
            }}
            batchTallies={{ file: null, processing: null }}
            cvrs={{ file: null, processing: null }}
            auditType="BALLOT_POLLING"
          />
        </Router>
      )
      screen.getByText('Round 1 of the audit is in progress.')
      screen.getByText('Audit boards not set up.')
    })

    it('renders 1st round in progress, audit boards set up, unfinished audited state', () => {
      render(
        <Router>
          <JurisdictionAdminStatusBox
            rounds={roundMocks.singleIncomplete}
            auditBoards={auditBoardMocks.unfinished}
            ballotManifest={{
              file: null,
              processing: fileProcessingMocks.processed,
            }}
            batchTallies={{ file: null, processing: null }}
            cvrs={{ file: null, processing: null }}
            auditType="BALLOT_POLLING"
          />
        </Router>
      )
      screen.getByText('Round 1 of the audit is in progress.')
      screen.getByText('0 of 1 audit boards complete.')
    })

    it('renders 1st round finished, incomplete audit state', () => {
      render(
        <Router>
          <JurisdictionAdminStatusBox
            rounds={roundMocks.singleIncomplete}
            auditBoards={auditBoardMocks.finished}
            ballotManifest={{
              file: null,
              processing: fileProcessingMocks.processed,
            }}
            batchTallies={{ file: null, processing: null }}
            cvrs={{ file: null, processing: null }}
            auditType="BALLOT_POLLING"
          />
        </Router>
      )
      screen.getByText('Round 1 of the audit is in progress.')
      screen.getByText('1 of 1 audit boards complete.')
      screen.getByText('Waiting for all jurisdictions to complete Round 1.')
    })

    it('renders completion in first round state', () => {
      render(
        <Router>
          <JurisdictionAdminStatusBox
            rounds={roundMocks.singleComplete}
            auditBoards={auditBoardMocks.finished}
            ballotManifest={{
              file: null,
              processing: fileProcessingMocks.processed,
            }}
            batchTallies={{ file: null, processing: null }}
            cvrs={{ file: null, processing: null }}
            auditType="BALLOT_POLLING"
          />
        </Router>
      )
      screen.getByText('The audit is complete')
      screen.getByText('Download the audit report.')
      screen.getByText('Download Audit Report')
    })

    it('downloads audit report', () => {
      window.open = jest.fn()
      render(
        <Router>
          <JurisdictionAdminStatusBox
            rounds={roundMocks.singleComplete}
            auditBoards={auditBoardMocks.finished}
            ballotManifest={{
              file: null,
              processing: fileProcessingMocks.processed,
            }}
            batchTallies={{ file: null, processing: null }}
            cvrs={{ file: null, processing: null }}
            auditType="BALLOT_POLLING"
          />
        </Router>
      )
      fireEvent.click(
        screen.getByRole('button', { name: 'Download Audit Report' }),
        {
          bubbles: true,
        }
      )
      expect(window.open).toHaveBeenCalledTimes(1)
      expect(window.open).toHaveBeenCalledWith(
        '/api/election/1/jurisdiction/1/report'
      )
    })
  })

  // TODO test BATCH_COMPARISON and BALLOT_COMPARISON audits
})
