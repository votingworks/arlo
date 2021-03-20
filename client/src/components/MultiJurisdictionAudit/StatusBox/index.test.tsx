import React from 'react'
import { BrowserRouter as Router, useParams } from 'react-router-dom'
import { render, fireEvent, screen, waitFor } from '@testing-library/react'
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
import { IAuditSettings } from '../useAuditSettings'

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

const cvrAuditTypes: IAuditSettings['auditType'][] = [
  'BALLOT_COMPARISON',
  'HYBRID',
]

describe('StatusBox', () => {
  describe('AuditAdminStatusBox', () => {
    it('renders initial state', () => {
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={[]}
            startNextRound={jest.fn()}
            jurisdictions={[]}
            contests={[]}
            auditSettings={auditSettings.blank!}
          />
        </Router>
      )

      // check if audit name is present
      screen.getByRole('heading', {
        name: 'Test Audit',
      })
      screen.getByText('Audit setup is not complete.')
      screen.getByText('The audit has not started.')
    })

    it('renders partial upload state', () => {
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={[]}
            startNextRound={jest.fn()}
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
            startNextRound={jest.fn()}
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

    cvrAuditTypes.forEach(auditType => {
      it(`renders ${auditType} audit, partial upload state`, () => {
        render(
          <Router>
            <AuditAdminStatusBox
              rounds={[]}
              startNextRound={jest.fn()}
              jurisdictions={jurisdictionMocks.allManifestsSomeCVRs}
              contests={[]}
              auditSettings={
                auditType === 'BALLOT_COMPARISON'
                  ? auditSettings.blankBallotComparison
                  : auditSettings.blankHybrid
              }
            />
          </Router>
        )
        screen.getByText('Audit setup is not complete.')
        screen.getByText('The audit has not started.')
        screen.getByText('1 of 3 jurisdictions have completed file uploads.')
      })

      it(`renders ${auditType} audit, full uploads state`, () => {
        render(
          <Router>
            <AuditAdminStatusBox
              rounds={[]}
              startNextRound={jest.fn()}
              jurisdictions={jurisdictionMocks.allManifestsWithCVRs}
              contests={[]}
              auditSettings={
                auditType === 'BALLOT_COMPARISON'
                  ? auditSettings.blankBallotComparison
                  : auditSettings.blankHybrid
              }
            />
          </Router>
        )
        screen.getByText('Audit setup is not complete.')
        screen.getByText('The audit has not started.')
        screen.getByText('3 of 3 jurisdictions have completed file uploads.')
      })
    })

    it(`renders BATCH_COMPARISON audit, partial upload state`, () => {
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={[]}
            startNextRound={jest.fn()}
            jurisdictions={jurisdictionMocks.twoManifestsOneTallies}
            contests={[]}
            auditSettings={auditSettings.blankBatch}
          />
        </Router>
      )
      screen.getByText('Audit setup is not complete.')
      screen.getByText('The audit has not started.')
      screen.getByText('1 of 3 jurisdictions have completed file uploads.')
    })

    it(`renders BATCH_COMPARISON audit, full uploads state`, () => {
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={[]}
            startNextRound={jest.fn()}
            jurisdictions={jurisdictionMocks.allManifestsAllTallies}
            contests={[]}
            auditSettings={auditSettings.blankBatch}
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
            startNextRound={jest.fn()}
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
            startNextRound={jest.fn()}
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
            startNextRound={jest.fn()}
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

    it('creates the next round', async () => {
      const startNextRoundMock = jest.fn()
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.needAnother}
            startNextRound={startNextRoundMock}
            jurisdictions={jurisdictionMocks.allComplete}
            contests={contestMocks.filledTargeted.contests}
            auditSettings={auditSettings.all}
          />
        </Router>
      )
      fireEvent.click(screen.getByRole('button', { name: 'Start Round 2' }), {
        bubbles: true,
      })

      expect(
        screen.getByRole('button', { name: 'Start Round 2' })
      ).toBeDisabled()
      await waitFor(() => expect(startNextRoundMock).toHaveBeenCalledTimes(1))
    })

    it('renders audit completion state', () => {
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.singleComplete}
            startNextRound={jest.fn()}
            jurisdictions={jurisdictionMocks.allComplete}
            contests={contestMocks.filledTargeted.contests}
            auditSettings={auditSettings.all}
          />
        </Router>
      )
      screen.getByText('Congratulations - the audit is complete!')
      screen.getByText('Download Audit Report')
    })

    it('downloads audit report', async () => {
      window.open = jest.fn()
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.singleComplete}
            startNextRound={jest.fn()}
            jurisdictions={jurisdictionMocks.allComplete}
            contests={contestMocks.filledTargeted.contests}
            auditSettings={auditSettings.all}
          />
        </Router>
      )
      const downloadReportButton = screen.getByRole('button', {
        name: 'Download Audit Report',
      })
      fireEvent.click(downloadReportButton, {
        bubbles: true,
      })
      await expect(downloadReportButton.classList.contains('bp3-loading')).toBe(
        true
      )
      await waitFor(() => {
        expect(window.open).toHaveBeenCalledTimes(1)
        expect(window.open).toBeCalledWith(`/api/election/1/report`)
      })
      expect(downloadReportButton.classList.contains('bp3-loading')).toBe(false)
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
            auditName="Test Audit"
          />
        </Router>
      )

      // check if audit name is present
      screen.getByRole('heading', {
        name: 'Test Audit',
      })
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
            auditName="Test Audit"
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
            auditName="Test Audit"
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
            auditName="Test Audit"
          />
        </Router>
      )
      screen.getByText('Round 1 of the audit is in progress.')
      screen.getByText('0 of 1 audit boards complete.')
    })

    it('renders 1st round auditing complete, audit board not signed off, incomplete audit state', () => {
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
            auditName="Test Audit"
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
            auditBoards={auditBoardMocks.signedOff}
            ballotManifest={{
              file: null,
              processing: fileProcessingMocks.processed,
            }}
            batchTallies={{ file: null, processing: null }}
            cvrs={{ file: null, processing: null }}
            auditType="BALLOT_POLLING"
            auditName="Test Audit"
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
            auditName="Test Audit"
          />
        </Router>
      )
      screen.getByText('The audit is complete')
      screen.getByText('Download the audit report.')
      screen.getByText('Download Audit Report')
    })

    it('downloads audit report', async () => {
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
            auditName="Test Audit"
          />
        </Router>
      )
      const downloadReportButton = screen.getByRole('button', {
        name: 'Download Audit Report',
      })
      fireEvent.click(downloadReportButton, {
        bubbles: true,
      })
      await expect(downloadReportButton.classList.contains('bp3-loading')).toBe(
        true
      )
      await waitFor(() => {
        expect(window.open).toHaveBeenCalledTimes(1)
        expect(window.open).toHaveBeenCalledWith(
          '/api/election/1/jurisdiction/1/report'
        )
      })
      await expect(downloadReportButton.classList.contains('bp3-loading')).toBe(
        false
      )
    })

    cvrAuditTypes.forEach(auditType => {
      it(`renders ${auditType} audit, CVRs not uploaded`, () => {
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
              auditType={auditType}
              auditName="Test Audit"
            />
          </Router>
        )
        screen.getByText('The audit has not started.')
        screen.getByText('1/2 files successfully uploaded.')
      })

      it(`renders ${auditType} audit, CVRs uploaded`, () => {
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
              cvrs={{
                file: null,
                processing: fileProcessingMocks.processed,
              }}
              auditType={auditType}
              auditName="Test Audit"
            />
          </Router>
        )
        screen.getByText('The audit has not started.')
        screen.getByText('2/2 files successfully uploaded.')
        screen.getByText('Waiting for Audit Administrator to launch audit.')
      })

      it(`renders ${auditType} audit, CVRs errored`, () => {
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
              cvrs={{
                file: null,
                processing: fileProcessingMocks.errored,
              }}
              auditType={auditType}
              auditName="Test Audit"
            />
          </Router>
        )
        screen.getByText('The audit has not started.')
        screen.getByText('1/2 files successfully uploaded.')
      })
    })

    it(`renders BATCH_COMPARISON audit, tallies not uploaded`, () => {
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
            auditType="BATCH_COMPARISON"
            auditName="Test Audit"
          />
        </Router>
      )
      screen.getByText('The audit has not started.')
      screen.getByText('1/2 files successfully uploaded.')
    })

    it(`renders BATCH_COMPARISON audit, tallies uploaded`, () => {
      render(
        <Router>
          <JurisdictionAdminStatusBox
            rounds={[]}
            auditBoards={[]}
            ballotManifest={{
              file: null,
              processing: fileProcessingMocks.processed,
            }}
            batchTallies={{
              file: null,
              processing: fileProcessingMocks.processed,
            }}
            cvrs={{ file: null, processing: null }}
            auditType="BATCH_COMPARISON"
            auditName="Test Audit"
          />
        </Router>
      )
      screen.getByText('The audit has not started.')
      screen.getByText('2/2 files successfully uploaded.')
      screen.getByText('Waiting for Audit Administrator to launch audit.')
    })

    it(`renders BATCH_COMPARISON audit, tallies errored`, () => {
      render(
        <Router>
          <JurisdictionAdminStatusBox
            rounds={[]}
            auditBoards={[]}
            ballotManifest={{
              file: null,
              processing: fileProcessingMocks.processed,
            }}
            batchTallies={{
              file: null,
              processing: fileProcessingMocks.errored,
            }}
            cvrs={{ file: null, processing: null }}
            auditType="BATCH_COMPARISON"
            auditName="Test Audit"
          />
        </Router>
      )
      screen.getByText('The audit has not started.')
      screen.getByText('1/2 files successfully uploaded.')
    })
  })
})
