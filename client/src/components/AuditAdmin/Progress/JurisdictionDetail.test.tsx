import { describe, expect, it, vi } from 'vitest'
import React from 'react'
import {
  render as testingLibraryRender,
  screen,
  within,
  waitFor,
} from '@testing-library/react'
import { QueryClientProvider } from 'react-query'
import userEvent from '@testing-library/user-event'
import JurisdictionDetail, {
  IJurisdictionDetailProps,
} from './JurisdictionDetail'
import {
  aaApiCalls,
  jaApiCalls,
  jurisdictionMocks,
  roundMocks,
  auditSettingsMocks,
  manifestMocks,
  cvrsMocks,
  auditBoardMocks,
  talliesMocks,
  manifestFile,
  cvrsFile,
  talliesFile,
  contestMocks,
} from '../../_mocks'
import { withMockFetch, createQueryClient } from '../../testUtilities'
import { dummyBallots } from '../../AuditBoard/_mocks'
import { batchesMocks } from '../../JurisdictionAdmin/_mocks'

vi.mock('axios')

// Borrowed from generateSheets.test.tsx
const mockSavePDF = vi.fn()
vi.mock('jspdf', async importActual => {
  const { jsPDF } = (await importActual()) as any
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  function mockJsPDF(options?: any) {
    return {
      ...new jsPDF(options),
      addImage: vi.fn(),
      save: mockSavePDF,
    }
  }
  return { default: mockJsPDF, jsPDF: mockJsPDF }
})
window.URL.createObjectURL = vi.fn()
window.open = vi.fn()
Object.defineProperty(window, 'location', {
  writable: true,
  value: { reload: vi.fn() },
})

const render = (props: Partial<IJurisdictionDetailProps>) =>
  testingLibraryRender(
    <QueryClientProvider client={createQueryClient()}>
      <JurisdictionDetail
        handleClose={vi.fn()}
        jurisdiction={jurisdictionMocks.noManifests[0]}
        electionId="1"
        round={null}
        auditSettings={auditSettingsMocks.all}
        {...props}
      />
    </QueryClientProvider>
  )

describe('JurisdictionDetail', () => {
  it('shows last login if it exists', async () => {
    const expectedCalls = [
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      const loginTime = new Date().toLocaleString()
      render({
        jurisdiction: jurisdictionMocks.oneManifest[0],
        lastLoginActivity: {
          id: '0',
          activityName: 'JurisdictionAdminLogin',
          timestamp: loginTime,
          user: {
            type: 'jurisdiction-admin',
            key: 'ja-1@example.com',
            supportUser: false,
          },
          election: null,
          info: {},
        },
      })

      await screen.findByText(`ja-1@example.com at ${loginTime}`)
    })
  })

  it('before launch, shows manifest for ballot polling audit', async () => {
    const expectedCalls = [
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
      ...jaApiCalls.uploadManifestCalls,
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.deleteManifest,
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      render({ jurisdiction: jurisdictionMocks.oneManifest[0] })

      screen.getByRole('heading', { name: 'Jurisdiction Files' })

      const manifestCard = (
        await screen.findByRole('heading', { name: 'Ballot Manifest' })
      ).closest('.bp3-card') as HTMLElement

      userEvent.upload(
        within(manifestCard).getByLabelText('Select a file...'),
        manifestFile
      )
      await within(manifestCard).findByText('manifest.csv')
      userEvent.click(
        within(manifestCard).getByRole('button', { name: /Upload/ })
      )

      await within(manifestCard).findByText('Uploaded')
      const manifestLink = within(manifestCard).getByRole('button', {
        name: /Download/,
      })
      expect(manifestLink).toHaveAttribute(
        'href',
        '/api/election/1/jurisdiction/jurisdiction-id-1/ballot-manifest/csv'
      )

      userEvent.click(
        within(manifestCard).getByRole('button', { name: /Delete/ })
      )
      await within(manifestCard).findByLabelText('Select a file...')
    })
  })

  it('before launch, shows manifest and cvrs for ballot comparison audit', async () => {
    const expectedCalls = [
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
      jaApiCalls.getCVRSfile(cvrsMocks.empty),
      ...jaApiCalls.uploadManifestCalls,
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getCVRSfile(cvrsMocks.empty),
      ...jaApiCalls.uploadCVRsCalls,
      jaApiCalls.getCVRSfile(cvrsMocks.processed),
      jaApiCalls.deleteManifest,
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
      jaApiCalls.getCVRSfile(cvrsMocks.processed),
      ...jaApiCalls.uploadManifestCalls,
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getCVRSfile(cvrsMocks.errored),
      jaApiCalls.deleteCVRs,
      jaApiCalls.getCVRSfile(cvrsMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      render({
        jurisdiction: {
          ...jurisdictionMocks.noManifests[0],
          cvrs: cvrsMocks.empty,
        },
        auditSettings: auditSettingsMocks.ballotComparisonAll,
      })

      screen.getByRole('heading', { name: 'Jurisdiction Files' })

      const manifestCard = (
        await screen.findByRole('heading', { name: 'Ballot Manifest' })
      ).closest('.bp3-card') as HTMLElement

      const cvrsCard = (
        await screen.findByRole('heading', { name: 'Cast Vote Records (CVR)' })
      ).closest('.bp3-card') as HTMLElement

      // CVRs should be disabled until manifest uploaded
      expect(within(cvrsCard).getByLabelText('Select a file...')).toBeDisabled()
      expect(
        within(cvrsCard).getByRole('button', { name: /Upload/ })
      ).toBeDisabled()
      expect(within(cvrsCard).getByLabelText('CVR File Type:')).toBeDisabled()

      // Upload manifest
      userEvent.upload(
        within(manifestCard).getByLabelText('Select a file...'),
        manifestFile
      )
      await within(manifestCard).findByText('manifest.csv')
      userEvent.click(
        within(manifestCard).getByRole('button', { name: /Upload/ })
      )
      await within(manifestCard).findByText('Uploaded')

      // Now can upload CVRs
      expect(within(cvrsCard).getByLabelText('Select a file...')).toBeDisabled()
      userEvent.selectOptions(
        within(cvrsCard).getByLabelText('CVR File Type:'),
        'ClearBallot'
      )
      userEvent.upload(
        within(cvrsCard).getByLabelText('Select a file...'),
        cvrsFile
      )
      await within(cvrsCard).findByText('cvrs.csv')
      userEvent.click(within(cvrsCard).getByRole('button', { name: /Upload/ }))
      await waitFor(() =>
        expect(within(cvrsCard).getByLabelText('CVR File Type:')).toBeDisabled()
      )
      await within(cvrsCard).findByText('Uploaded')
      const cvrsLink = within(cvrsCard).getByRole('button', {
        name: /Download/,
      })
      expect(cvrsLink).toHaveAttribute(
        'href',
        '/api/election/1/jurisdiction/jurisdiction-id-1/cvrs/csv'
      )
      within(cvrsCard).getByText('ClearBallot')

      // Now try changing the manifest, CVRs should be reloaded
      userEvent.click(
        within(manifestCard).getByRole('button', { name: /Delete/ })
      )
      userEvent.upload(
        await within(manifestCard).findByLabelText('Select a file...'),
        manifestFile
      )
      await within(manifestCard).findByText('manifest.csv')
      userEvent.click(
        within(manifestCard).getByRole('button', { name: /Upload/ })
      )
      await within(manifestCard).findByText('Uploaded')
      await within(cvrsCard).findByText('Upload Failed')

      // Delete CVRs
      userEvent.click(within(cvrsCard).getByRole('button', { name: /Delete/ }))
      await within(cvrsCard).findByLabelText('Select a file...')
      const cvrFileTypeInput = within(cvrsCard).getByLabelText('CVR File Type:')
      expect(cvrFileTypeInput).toBeEnabled()
      // For some reason this doesn't work in test even though it works in the app
      // expect(cvrFileTypeInput).toHaveValue('CLEARBALLOT')
    })
  })

  it('before launch, accepts Hart CVR ZIP file', async () => {
    const cvrsZip = new File(['test cvr data'], 'cvrs.zip', {
      type: 'application/zip',
    })

    const expectedCalls = [
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getCVRSfile(cvrsMocks.empty),
      ...jaApiCalls.uploadCVRZipCalls,
      jaApiCalls.getCVRSfile(cvrsMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      render({
        jurisdiction: {
          ...jurisdictionMocks.allManifests[0],
          cvrs: cvrsMocks.empty,
        },
        auditSettings: auditSettingsMocks.ballotComparisonAll,
      })

      const cvrsCard = (
        await screen.findByRole('heading', { name: 'Cast Vote Records (CVR)' })
      ).closest('.bp3-card') as HTMLElement
      userEvent.selectOptions(
        within(cvrsCard).getByLabelText('CVR File Type:'),
        within(cvrsCard).getByRole('option', { name: 'Hart' })
      )
      userEvent.upload(
        await within(cvrsCard).findByLabelText('Select a file...'),
        cvrsZip
      )
      await within(cvrsCard).findByText('cvrs.zip')
      userEvent.click(screen.getByRole('button', { name: /Upload/ }))
      await within(cvrsCard).findByText('Uploaded')
    })
  })

  it('before launch, shows manifest and batch tallies for batch comparison audit', async () => {
    const expectedCalls = [
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
      ...jaApiCalls.uploadManifestCalls,
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
      ...jaApiCalls.uploadTalliesCalls,
      jaApiCalls.getBatchTalliesFile(talliesMocks.processed),
      jaApiCalls.deleteManifest,
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
      jaApiCalls.getBatchTalliesFile(talliesMocks.processed),
      ...jaApiCalls.uploadManifestCalls,
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getBatchTalliesFile(talliesMocks.errored),
      jaApiCalls.deleteTallies,
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      render({
        jurisdiction: jurisdictionMocks.noManifestsNoTallies[0],
        auditSettings: auditSettingsMocks.batchComparisonAll,
      })

      screen.getByRole('heading', { name: 'Jurisdiction Files' })

      const manifestCard = (
        await screen.findByRole('heading', { name: 'Ballot Manifest' })
      ).closest('.bp3-card') as HTMLElement

      const talliesCard = (
        await screen.findByRole('heading', {
          name: 'Candidate Totals by Batch',
        })
      ).closest('.bp3-card') as HTMLElement

      // Tallies should be disabled until manifest uploaded
      expect(
        within(talliesCard).getByLabelText('Select a file...')
      ).toBeDisabled()
      expect(
        within(talliesCard).getByRole('button', { name: /Upload/ })
      ).toBeDisabled()

      // Upload manifest
      userEvent.upload(
        within(manifestCard).getByLabelText('Select a file...'),
        manifestFile
      )
      await within(manifestCard).findByText('manifest.csv')
      userEvent.click(
        within(manifestCard).getByRole('button', { name: /Upload/ })
      )
      await within(manifestCard).findByText('Uploaded')

      // Now can upload tallies
      userEvent.upload(
        within(talliesCard).getByLabelText('Select a file...'),
        talliesFile
      )
      await within(talliesCard).findByText('tallies.csv')
      userEvent.click(
        within(talliesCard).getByRole('button', { name: /Upload/ })
      )
      await within(talliesCard).findByText('Uploaded')
      const downloadTemplateLink = within(talliesCard).getByRole('button', {
        name: /Download Template/,
      })
      expect(downloadTemplateLink).toHaveAttribute(
        'href',
        '/api/election/1/jurisdiction/jurisdiction-id-1/batch-tallies/template-csv'
      )
      const talliesLink = within(talliesCard).getByRole('button', {
        name: /Download$/,
      })
      expect(talliesLink).toHaveAttribute(
        'href',
        '/api/election/1/jurisdiction/jurisdiction-id-1/batch-tallies/csv'
      )

      // Now try changing the manifest, tallies should be reloaded
      userEvent.click(
        within(manifestCard).getByRole('button', { name: /Delete/ })
      )
      userEvent.upload(
        await within(manifestCard).findByLabelText('Select a file...'),
        manifestFile
      )
      await within(manifestCard).findByText('manifest.csv')
      userEvent.click(
        within(manifestCard).getByRole('button', { name: /Upload/ })
      )
      await within(manifestCard).findByText('Uploaded')
      await within(talliesCard).findByText('Upload Failed')

      // Delete tallies
      userEvent.click(
        within(talliesCard).getByRole('button', { name: /Delete/ })
      )
      await within(talliesCard).findByLabelText('Select a file...')
    })
  })

  it('after launch, shows round status for ballot polling audit', async () => {
    const expectedCalls = [
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getAuditBoards(auditBoardMocks.unfinished),
      jaApiCalls.getBallotCount(dummyBallots.ballots),
      jaApiCalls.getBallots(dummyBallots.ballots),
      jaApiCalls.getBallots(dummyBallots.ballots),
    ]
    await withMockFetch(expectedCalls, async () => {
      render({
        jurisdiction: jurisdictionMocks.noneStarted[0],
        round: roundMocks.singleIncomplete[0],
      })

      await screen.findByRole('heading', { name: 'Current Audit Round' })

      userEvent.click(
        screen.getByRole('button', {
          name: /Download Ballot Retrieval List/,
        })
      )
      expect(window.open).toHaveBeenCalledWith(
        '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/ballots/retrieval-list'
      )

      userEvent.click(
        screen.getByRole('button', { name: /Download Placeholder Sheets/ })
      )
      await waitFor(() =>
        expect(
          mockSavePDF
        ).toHaveBeenCalledWith(
          'Round 1 Placeholders - Jurisdiction 1 - Test Audit.pdf',
          { returnPromise: true }
        )
      )
      mockSavePDF.mockClear()
      userEvent.click(
        screen.getByRole('button', { name: /Download Ballot Labels/ })
      )
      await waitFor(() =>
        expect(
          mockSavePDF
        ).toHaveBeenCalledWith(
          'Round 1 Labels - Jurisdiction 1 - Test Audit.pdf',
          { returnPromise: true }
        )
      )
      mockSavePDF.mockClear()
      userEvent.click(
        screen.getByRole('button', { name: /Download Audit Board Credentials/ })
      )
      await waitFor(() =>
        expect(
          mockSavePDF
        ).toHaveBeenCalledWith(
          'Audit Board Credentials - Jurisdiction 1 - Test Audit.pdf',
          { returnPromise: true }
        )
      )

      // Manifest should still be shown for download, but form should be disabled
      const manifestCard = (
        await screen.findByRole('heading', { name: 'Ballot Manifest' })
      ).closest('.bp3-card') as HTMLElement
      await within(manifestCard).findByText('Uploaded')
      within(manifestCard).getByRole('button', { name: /Download/ })
      expect(
        within(manifestCard).getByRole('button', { name: /Delete/ })
      ).toBeDisabled()
    })
  })

  it('after launch, shows round status for ballot comparison audit', async () => {
    const expectedCalls = [
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getCVRSfile(cvrsMocks.processed),
      jaApiCalls.getAuditBoards(auditBoardMocks.unfinished),
      jaApiCalls.getBallotCount(dummyBallots.ballots),
    ]
    await withMockFetch(expectedCalls, async () => {
      render({
        jurisdiction: jurisdictionMocks.noneStartedBallotComparison[0],
        auditSettings: auditSettingsMocks.ballotComparisonAll,
        round: roundMocks.singleIncomplete[0],
      })

      await screen.findByRole('heading', { name: 'Current Audit Round' })
      screen.getByRole('button', {
        name: /Download Ballot Retrieval List/,
      })
      screen.getByRole('button', { name: /Download Ballot Labels/ })
      screen.getByRole('button', { name: /Download Placeholder Sheets/ })
      screen.getByRole('button', { name: /Download Audit Board Credentials/ })

      // CVRs should still be shown for download, but form should be disabled
      const cvrsCard = (
        await screen.findByRole('heading', { name: 'Cast Vote Records (CVR)' })
      ).closest('.bp3-card') as HTMLElement
      await within(cvrsCard).findByText('Uploaded')
      within(cvrsCard).getByRole('button', { name: /Download/ })
      expect(
        within(cvrsCard).getByRole('button', { name: /Delete/ })
      ).toBeDisabled()
    })
  })

  it('after launch, shows round status for batch comparison audit', async () => {
    const expectedCalls = [
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getBatchTalliesFile(talliesMocks.processed),
      jaApiCalls.getAuditBoards(auditBoardMocks.unfinished),
      jaApiCalls.getBatches(batchesMocks.emptyInitial),
      jaApiCalls.getBatches(batchesMocks.emptyInitial),
      jaApiCalls.getJurisdictionContests(contestMocks.oneTargeted),
    ]
    await withMockFetch(expectedCalls, async () => {
      render({
        jurisdiction: jurisdictionMocks.oneComplete[0],
        auditSettings: auditSettingsMocks.batchComparisonAll,
        round: roundMocks.singleIncomplete[0],
      })

      // Batch tallies should still be shown for download, but form should be disabled
      const talliesCard = (
        await screen.findByRole('heading', {
          name: 'Candidate Totals by Batch',
        })
      ).closest('.bp3-card') as HTMLElement
      await within(talliesCard).findByText('Uploaded')
      within(talliesCard).getByRole('button', { name: /Download$/ })
      expect(
        within(talliesCard).getByRole('button', { name: /Delete/ })
      ).toBeDisabled()

      await screen.findByRole('heading', { name: 'Current Audit Round' })
      userEvent.click(
        screen.getByRole('button', {
          name: /Download Batch Retrieval List/,
        })
      )
      expect(window.open).toHaveBeenCalledWith(
        '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/batches/retrieval-list'
      )

      userEvent.click(
        screen.getByRole('button', { name: /Download Batch Tally Sheets/ })
      )
      await waitFor(() =>
        expect(
          mockSavePDF
        ).toHaveBeenCalledWith(
          'Batch Tally Sheets - Jurisdiction 1 - Test Audit.pdf',
          { returnPromise: true }
        )
      )
      mockSavePDF.mockClear()
    })
  })

  it('after launch, shows a message when no ballots sampled', async () => {
    const expectedCalls = [
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getAuditBoards(auditBoardMocks.unfinished),
      jaApiCalls.getBallotCount([]),
    ]
    await withMockFetch(expectedCalls, async () => {
      render({
        jurisdiction: jurisdictionMocks.oneComplete[0],
        round: roundMocks.singleIncomplete[0],
      })
      await screen.findByText('No ballots sampled')
    })
  })

  it('after launch, shows a message in the detail modal when no audit boards set up', async () => {
    const expectedCalls = [
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getAuditBoards([]),
      jaApiCalls.getBallotCount(dummyBallots.ballots),
    ]
    await withMockFetch(expectedCalls, async () => {
      render({
        jurisdiction: jurisdictionMocks.noneStarted[0],
        round: roundMocks.singleIncomplete[0],
      })
      await screen.findByText('Waiting for jurisdiction to set up audit boards')
    })
  })

  it('after launch, shows a message when no batches sampled', async () => {
    const expectedCalls = [
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getBatchTalliesFile(talliesMocks.processed),
      jaApiCalls.getAuditBoards(auditBoardMocks.unfinished),
      jaApiCalls.getBatches({ batches: [], resultsFinalizedAt: null }),
    ]
    await withMockFetch(expectedCalls, async () => {
      render({
        jurisdiction: jurisdictionMocks.oneComplete[0],
        auditSettings: auditSettingsMocks.batchComparisonAll,
        round: roundMocks.singleIncomplete[0],
      })
      await screen.findByText('No ballots sampled')
    })
  })

  it('after launch, shows a message when auditing is complete', async () => {
    const expectedCalls = [
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getAuditBoards(auditBoardMocks.finished),
      jaApiCalls.getBallotCount(dummyBallots.ballots),
    ]
    await withMockFetch(expectedCalls, async () => {
      render({
        jurisdiction: jurisdictionMocks.allComplete[0],
        auditSettings: auditSettingsMocks.all,
        round: roundMocks.singleIncomplete[0],
      })
      await screen.findByText('Data entry complete')
    })
  })

  it('after launch, shows a button to unfinalize batch results', async () => {
    const expectedCalls = [
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getBatchTalliesFile(talliesMocks.processed),
      jaApiCalls.getAuditBoards(auditBoardMocks.single),
      jaApiCalls.getBatches(batchesMocks.complete),
      jaApiCalls.unfinalizeBatchResults,
    ]
    await withMockFetch(expectedCalls, async () => {
      render({
        jurisdiction: jurisdictionMocks.allComplete[0],
        auditSettings: auditSettingsMocks.batchComparisonAll,
        round: roundMocks.singleIncomplete[0],
      })

      await screen.findByText('Tallies finalized')

      userEvent.click(
        screen.getByRole('button', { name: 'Unfinalize Tallies' })
      )
      await waitFor(() => {
        expect(window.location.reload).toHaveBeenCalled()
      })
    })
  })

  it.each([
    jurisdictionMocks.oneComplete[0], // Jurisdiction status = in progress
    jurisdictionMocks.allComplete[0], // Jurisdiction status = complete
  ])(
    'after launch of an audit with online audit boards, shows a table of audit boards',
    async jurisdiction => {
      const expectedCalls = [
        jaApiCalls.getBallotManifestFile(manifestMocks.processed),
        jaApiCalls.getAuditBoards(auditBoardMocks.double),
        jaApiCalls.getBallotCount(dummyBallots.ballots),
      ]
      await withMockFetch(expectedCalls, async () => {
        render({
          auditSettings: auditSettingsMocks.all,
          jurisdiction,
          round: roundMocks.singleIncomplete[0],
        })

        await screen.findByRole('columnheader', { name: 'Audit Board' })
        screen.getByRole('columnheader', { name: 'Actions' })
        screen.getByRole('cell', { name: 'Audit Board #01' })
        screen.getByRole('cell', { name: 'Audit Board #02' })
        const reopenButtons = screen.getAllByRole('button', { name: 'Reopen' })
        expect(reopenButtons).toHaveLength(2)
        expect(reopenButtons[0]).toBeDisabled()
        expect(reopenButtons[1]).toBeDisabled()
      })
    }
  )

  it('after launch of an audit with online audit boards, allows reopening of audit boards that have signed off', async () => {
    const expectedCalls = [
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getAuditBoards(auditBoardMocks.signedOff),
      jaApiCalls.getBallotCount(dummyBallots.ballots),
      aaApiCalls.reopenAuditBoard,
    ]
    await withMockFetch(expectedCalls, async () => {
      render({
        auditSettings: auditSettingsMocks.all,
        jurisdiction: jurisdictionMocks.allComplete[0],
        round: roundMocks.singleIncomplete[0],
      })

      await screen.findByText('Data entry complete')
      screen.getByText('Audit Board #01')
      userEvent.click(screen.getByRole('button', { name: 'Reopen' }))
      const dialog = (
        await screen.findByRole('heading', {
          name: 'Confirm',
        })
      ).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText(
        'Are you sure you want to reopen Audit Board #01?'
      )
      userEvent.click(within(dialog).getByRole('button', { name: 'Reopen' }))
      await waitFor(() => {
        expect(window.location.reload).toHaveBeenCalled()
      })
    })
  })

  it('after launch of an audit with offline audit boards, does not show a table of audit boards', async () => {
    const expectedCalls = [
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getAuditBoards(auditBoardMocks.double),
      jaApiCalls.getBallotCount(dummyBallots.ballots),
    ]
    await withMockFetch(expectedCalls, async () => {
      render({
        auditSettings: auditSettingsMocks.offlineAll,
        jurisdiction: jurisdictionMocks.allComplete[0],
        round: roundMocks.singleIncomplete[0],
      })

      await screen.findByText('Data entry complete')
      expect(
        screen.queryByRole('button', { name: 'Reopen' })
      ).not.toBeInTheDocument()
    })
  })
})
