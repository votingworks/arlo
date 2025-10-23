import { describe, expect, it, vi } from 'vitest'
import React from 'react'
import { BrowserRouter as Router, useParams } from 'react-router-dom'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClientProvider } from 'react-query'
import { ToastContainer } from 'react-toastify'
import { AuditAdminStatusBox } from './StatusBox'
import { IAuditSettings } from '../useAuditSettings'
import {
  withMockFetch,
  createQueryClient,
  findAndCloseToast,
} from '../testUtilities'
import {
  aaApiCalls,
  auditSettingsMocks,
  jurisdictionMocks,
  contestMocks,
  roundMocks,
} from '../_mocks'
import { sampleSizeMock } from '../AuditAdmin/Setup/Review/_mocks'
import { FileProcessingStatus } from '../useCSV'

vi.mock(import('react-router-dom'), async importActual => ({
  ...(await importActual()), // use actual for all non-hook parts
  useRouteMatch: vi.fn(),
  useParams: vi.fn(),
}))
const paramsMock = vi.mocked(useParams)
paramsMock.mockReturnValue({
  electionId: '1',
  jurisdictionId: '1',
  view: 'setup',
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
            startNextRound={vi.fn()}
            finishRound={vi.fn()}
            undoRoundStart={vi.fn()}
            jurisdictions={[]}
            contests={[]}
            auditSettings={auditSettingsMocks.blank!}
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
            startNextRound={vi.fn()}
            finishRound={vi.fn()}
            undoRoundStart={vi.fn()}
            jurisdictions={jurisdictionMocks.oneManifest}
            contests={[]}
            auditSettings={auditSettingsMocks.blank!}
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
            startNextRound={vi.fn()}
            finishRound={vi.fn()}
            undoRoundStart={vi.fn()}
            jurisdictions={jurisdictionMocks.allManifests}
            contests={[]}
            auditSettings={auditSettingsMocks.blank!}
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
              startNextRound={vi.fn()}
              finishRound={vi.fn()}
              undoRoundStart={vi.fn()}
              jurisdictions={jurisdictionMocks.allManifestsSomeCVRs}
              contests={[]}
              auditSettings={
                auditType === 'BALLOT_COMPARISON'
                  ? auditSettingsMocks.blankBallotComparison
                  : auditSettingsMocks.blankHybrid
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
              startNextRound={vi.fn()}
              finishRound={vi.fn()}
              undoRoundStart={vi.fn()}
              jurisdictions={jurisdictionMocks.allManifestsWithCVRs}
              contests={[]}
              auditSettings={
                auditType === 'BALLOT_COMPARISON'
                  ? auditSettingsMocks.blankBallotComparison
                  : auditSettingsMocks.blankHybrid
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
            startNextRound={vi.fn()}
            finishRound={vi.fn()}
            undoRoundStart={vi.fn()}
            jurisdictions={jurisdictionMocks.twoManifestsOneTallies}
            contests={[]}
            auditSettings={auditSettingsMocks.blankBatch}
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
            startNextRound={vi.fn()}
            finishRound={vi.fn()}
            undoRoundStart={vi.fn()}
            jurisdictions={jurisdictionMocks.allManifestsAllTallies}
            contests={[]}
            auditSettings={auditSettingsMocks.blankBatch}
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
            startNextRound={vi.fn()}
            finishRound={vi.fn()}
            undoRoundStart={vi.fn()}
            jurisdictions={jurisdictionMocks.allManifests}
            contests={contestMocks.filledTargeted}
            auditSettings={auditSettingsMocks.all}
          />
        </Router>
      )
      screen.getByText('Audit setup is complete.')
      screen.getByText('The audit has not started.')
      screen.getByText('3 of 3 jurisdictions have completed file uploads.')
    })

    it('renders just launched round one state', () => {
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.singleIncomplete}
            startNextRound={vi.fn()}
            finishRound={vi.fn()}
            undoRoundStart={vi.fn()}
            jurisdictions={jurisdictionMocks.noneStarted}
            contests={contestMocks.filledTargeted}
            auditSettings={auditSettingsMocks.all}
          />
        </Router>
      )
      screen.getByText('Round 1 of the audit is in progress')
      screen.getByText('1 of 3 jurisdictions have completed round 1')
      screen.getByRole('button', { name: 'Undo Audit Launch' })
    })

    it('renders one of two jurisdictions done round one state', () => {
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.singleIncomplete}
            startNextRound={vi.fn()}
            finishRound={vi.fn()}
            undoRoundStart={vi.fn()}
            jurisdictions={jurisdictionMocks.oneComplete}
            contests={contestMocks.filledTargeted}
            auditSettings={auditSettingsMocks.all}
          />
        </Router>
      )
      screen.getByText('Round 1 of the audit is in progress')
      screen.getByText('1 of 3 jurisdictions have completed round 1')
      expect(screen.queryByRole('button')).not.toBeInTheDocument()
    })

    it('renders finish round button when all jurisdictions complete', async () => {
      const finishRoundMock = vi.fn()
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.singleIncomplete}
            startNextRound={vi.fn()}
            finishRound={finishRoundMock}
            undoRoundStart={vi.fn()}
            jurisdictions={jurisdictionMocks.allComplete}
            contests={contestMocks.filledTargeted}
            auditSettings={auditSettingsMocks.all}
          />
        </Router>
      )
      screen.getByText('Round 1 of the audit is in progress')
      screen.getByText('3 of 3 jurisdictions have completed round 1')
      userEvent.click(screen.getByRole('button', { name: 'Finish Round 1' }))
      await waitFor(() => expect(finishRoundMock).toHaveBeenCalledTimes(1))
    })

    it('renders round complete, need another round state', async () => {
      vi.useFakeTimers()
      const expectedCalls = [
        {
          ...aaApiCalls.getSampleSizes(sampleSizeMock.calculating),
          url: '/api/election/1/sample-sizes/2',
        },
        {
          ...aaApiCalls.getSampleSizes(sampleSizeMock.ballotComparison),
          url: '/api/election/1/sample-sizes/2',
        },
      ]
      await withMockFetch(expectedCalls, async () => {
        const startNextRoundMock = vi.fn()
        render(
          <QueryClientProvider client={createQueryClient()}>
            <Router>
              <AuditAdminStatusBox
                rounds={roundMocks.needAnother}
                startNextRound={startNextRoundMock}
                finishRound={vi.fn()}
                undoRoundStart={vi.fn()}
                jurisdictions={jurisdictionMocks.allComplete}
                contests={contestMocks.filledTargeted}
                auditSettings={auditSettingsMocks.ballotComparisonAll}
              />
              <ToastContainer />
            </Router>
          </QueryClientProvider>
        )
        screen.getByText(
          'Round 1 of the audit is complete - another round is needed'
        )
        await screen.findByText('Loading sample sizes...')

        const startRound2Button = screen.getByRole('button', {
          name: 'Start Round 2',
        })
        userEvent.click(startRound2Button)
        await findAndCloseToast('Sample sizes are still loading')

        vi.advanceTimersByTime(1000)

        await screen.findByText('Round 2 Sample Sizes')
        screen.getByText(/Contest Name: 15 ballots/)

        userEvent.click(startRound2Button)
        expect(startRound2Button).toBeDisabled()
        await waitFor(() => expect(startNextRoundMock).toHaveBeenCalledTimes(1))
        expect(startNextRoundMock).toHaveBeenCalledWith({
          'contest-id': sampleSizeMock.ballotComparison.sampleSizes![
            'contest-id'
          ][0],
        })
      })
      vi.useRealTimers()
    })

    it('renders round complete, need another round state for batch comparison audits', async () => {
      const expectedCalls = [
        {
          ...aaApiCalls.getSampleSizes(sampleSizeMock.batchComparison),
          url: '/api/election/1/sample-sizes/2',
        },
      ]
      await withMockFetch(expectedCalls, async () => {
        const startNextRoundMock = vi.fn()
        render(
          <QueryClientProvider client={createQueryClient()}>
            <Router>
              <AuditAdminStatusBox
                rounds={roundMocks.needAnother}
                startNextRound={startNextRoundMock}
                finishRound={vi.fn()}
                undoRoundStart={vi.fn()}
                jurisdictions={jurisdictionMocks.allComplete}
                contests={contestMocks.filledTargeted}
                auditSettings={auditSettingsMocks.batchComparisonAll}
              />
            </Router>
          </QueryClientProvider>
        )
        screen.getByText(
          'Round 1 of the audit is complete - another round is needed'
        )
        await screen.findByText('Round 2 Sample Sizes')
        screen.getByText(/Contest Name: 4 batches/)
      })
    })

    it('handles sample size errors in need another round state', async () => {
      const expectedCalls = [
        {
          ...aaApiCalls.getSampleSizes,
          url: '/api/election/1/sample-sizes/2',
          response: {
            sampleSizes: null,
            selected: null,
            task: {
              status: FileProcessingStatus.ERRORED,
              startedAt: '2019-07-18T16:34:07.000+00:00',
              completedAt: '2019-07-18T16:35:07.000+00:00',
              error: 'something went wrong',
            },
          },
        },
      ]
      await withMockFetch(expectedCalls, async () => {
        render(
          <QueryClientProvider client={createQueryClient()}>
            <Router>
              <AuditAdminStatusBox
                rounds={roundMocks.needAnother}
                startNextRound={vi.fn()}
                finishRound={vi.fn()}
                undoRoundStart={vi.fn()}
                jurisdictions={jurisdictionMocks.allComplete}
                contests={contestMocks.filledTargeted}
                auditSettings={auditSettingsMocks.ballotComparisonAll}
              />
            </Router>
          </QueryClientProvider>
        )
        await screen.findByText(
          'Error computing sample sizes: something went wrong'
        )
      })
    })

    it('renders audit completion state', () => {
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.singleComplete}
            startNextRound={vi.fn()}
            finishRound={vi.fn()}
            undoRoundStart={vi.fn()}
            jurisdictions={jurisdictionMocks.allComplete}
            contests={contestMocks.filledTargeted}
            auditSettings={auditSettingsMocks.all}
          />
        </Router>
      )
      screen.getByText('Congratulations - the audit is complete!')
      screen.getByText('Download Audit Report')
    })

    it('downloads audit report', async () => {
      const mockDownloadWindow: { onbeforeunload?: () => void } = {}
      window.open = vi.fn().mockReturnValue(mockDownloadWindow)
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={roundMocks.singleComplete}
            startNextRound={vi.fn()}
            finishRound={vi.fn()}
            undoRoundStart={vi.fn()}
            jurisdictions={jurisdictionMocks.allComplete}
            contests={contestMocks.filledTargeted}
            auditSettings={auditSettingsMocks.all}
          />
        </Router>
      )
      const downloadReportButton = screen.getByRole('button', {
        name: 'Download Audit Report',
      })
      userEvent.click(downloadReportButton)
      expect(downloadReportButton).toBeDisabled()
      await waitFor(() => {
        expect(window.open).toHaveBeenCalledTimes(1)
        expect(window.open).toBeCalledWith(`/api/election/1/report`)
      })
      mockDownloadWindow.onbeforeunload!()
      await waitFor(() => {
        expect(downloadReportButton).toBeEnabled()
      })
    })

    it('shows a message when a full hand tally is required', () => {
      render(
        <Router>
          <AuditAdminStatusBox
            rounds={[
              { ...roundMocks.singleIncomplete[0], needsFullHandTally: true },
            ]}
            startNextRound={vi.fn()}
            finishRound={vi.fn()}
            undoRoundStart={vi.fn()}
            jurisdictions={jurisdictionMocks.noneStarted}
            contests={contestMocks.filledTargeted}
            auditSettings={auditSettingsMocks.all}
          />
        </Router>
      )
      screen.getByText('Round 1 of the audit is in progress')
      screen.getByText('1 of 3 jurisdictions have completed round 1')
      screen.getByText('Full hand tally required')
      screen.getByText(
        'One or more target contests require a full hand tally to complete the audit.'
      )
    })
  })
})
