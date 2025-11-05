import { beforeEach, describe, expect, it, vi } from 'vitest'
import React from 'react'
import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ToastContainer } from 'react-toastify'
import { useParams } from 'react-router-dom'
import AuthDataProvider, { useAuthDataContext } from '../UserContext'
import JurisdictionAdminView from './JurisdictionAdminView'
import { renderWithRouter, withMockFetch, serverError } from '../testUtilities'
import {
  jaApiCalls,
  auditSettingsMocks,
  manifestMocks,
  talliesMocks,
  manifestFile,
  talliesFile,
  cvrsMocks,
  cvrsFile,
  roundMocks,
} from '../_mocks'

vi.mock(import('react-router-dom'), async importActual => ({
  ...(await importActual()), // use actual for all non-hook parts
  useRouteMatch: vi.fn(),
  useParams: vi.fn(),
}))
const paramsMock = vi.mocked(useParams)

vi.mock(import('axios'))

describe('JA setup', () => {
  // JurisdictionAdminView will only be rendered once the user is logged in, so
  // we simulate that.
  const JurisdictionAdminViewWithAuth: React.FC = () => {
    const auth = useAuthDataContext()
    return auth ? <JurisdictionAdminView /> : null
  }

  const renderView = () =>
    renderWithRouter(
      <AuthDataProvider>
        <JurisdictionAdminViewWithAuth />
        <ToastContainer />
      </AuthDataProvider>,
      {
        route: '/election/1/jurisdiction/jurisdiction-id-1/setup',
      }
    )

  beforeEach(() => {
    paramsMock.mockReturnValue({
      electionId: '1',
      jurisdictionId: 'jurisdiction-id-1',
      view: 'setup',
    })
  })

  it('renders setup screen', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettingsMocks.batchComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Setup')
      screen.getByText(/Jurisdiction One/)
      screen.getByText(/audit one/)
    })
  })

  it('submits ballot manifest and deletes it', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettingsMocks.all),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
      ...jaApiCalls.uploadManifestCalls,
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.deleteManifest,
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Setup')

      const uploadButton = screen.getByRole('button', { name: 'Upload File' })
      userEvent.click(uploadButton)
      await screen.findByText('You must upload a file')

      userEvent.upload(screen.getByLabelText('Select a file...'), manifestFile)
      userEvent.click(uploadButton)
      await screen.findByText('Uploaded at 6/8/2020, 9:39:14 PM.')
      screen.getByText('Audit setup complete')

      // We test delete after submit so that we can check that the input is
      // cleared of the originally submitted file
      const deleteButton = await screen.findByRole('button', {
        name: 'Delete File',
      })
      userEvent.click(deleteButton)
      await screen.findByRole('button', { name: 'Upload File' })
      screen.getByLabelText('Select a file...')
    })
  })

  it('submits batch tallies', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettingsMocks.batchComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
      ...jaApiCalls.uploadTalliesCalls,
      jaApiCalls.getBatchTalliesFile(talliesMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Setup')
      const talliesInput = screen.getByLabelText('Select a file...')
      const talliesButton = screen.getByRole('button', { name: 'Upload File' })
      const talliesTemplateButton = screen.getAllByRole('button', {
        name: 'Download Template',
      })[1]
      expect(talliesTemplateButton).toHaveAttribute(
        'href',
        '/api/election/1/jurisdiction/jurisdiction-id-1/batch-tallies/template-csv'
      )

      userEvent.click(talliesButton)
      await screen.findByText('You must upload a file')

      userEvent.upload(talliesInput, talliesFile)
      userEvent.click(talliesButton)
      await screen.findByText('Uploaded at 7/8/2020, 9:39:14 PM.')
      screen.getByText('Audit setup complete')

      // Verify that ballot manifests and candidate totals by batch can be replaced or deleted
      // after upload, and that templates can still be downloaded
      expect(
        screen.getAllByRole('button', { name: 'Replace File' })
      ).toHaveLength(2)
      expect(
        screen.getAllByRole('button', { name: 'Delete File' })
      ).toHaveLength(2)
      expect(
        screen.getAllByRole('button', { name: 'Download Template' })
      ).toHaveLength(2)
    })
  })

  it('toasts error when uploading batch tallies', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettingsMocks.batchComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
      jaApiCalls.uploadTalliesCalls[0],
      jaApiCalls.uploadTalliesCalls[1],
      serverError('postTallies', jaApiCalls.uploadTalliesCalls[2]),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Setup')
      userEvent.upload(screen.getByLabelText('Select a file...'), talliesFile)
      userEvent.click(screen.getByRole('button', { name: 'Upload File' }))
      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('something went wrong: postTallies')
    })
  })

  it('displays errors on invalid batch tallies upload', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettingsMocks.batchComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getBatchTalliesFile(talliesMocks.processed),
      ...jaApiCalls.uploadTalliesCalls,
      jaApiCalls.getBatchTalliesFile(talliesMocks.errored),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Setup')
      expect(screen.getAllByText(/Uploaded/)).toHaveLength(2)

      // Replace & upload errored batch tallies
      userEvent.click(
        screen.getAllByRole('button', {
          name: 'Replace File',
        })[1]
      )
      userEvent.upload(
        await screen.findByLabelText('Select a file...'),
        talliesFile
      )
      userEvent.click(screen.getByRole('button', { name: 'Upload File' }))
      await screen.findByText('Invalid CSV')
    })
  })

  it('displays errors after reprocessing batch tallies on replacing manifest', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettingsMocks.batchComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
      jaApiCalls.getBatchTalliesFile(talliesMocks.processed),
      ...jaApiCalls.uploadManifestCalls,
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getBatchTalliesFile(talliesMocks.errored),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Setup')

      // Upload a new manifest
      userEvent.click(
        screen.getAllByRole('button', { name: 'Replace File' })[0]
      )
      userEvent.upload(
        await screen.findByLabelText('Select a file...'),
        manifestFile
      )
      userEvent.click(screen.getByRole('button', { name: 'Upload File' }))
      await screen.findByText(/Uploaded/)
      await screen.findByText('Invalid CSV')
    })
  })

  it('submits CVRs', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettingsMocks.ballotComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getCVRSfile(cvrsMocks.empty),
      ...jaApiCalls.uploadCVRsCalls,
      jaApiCalls.getCVRSfile(cvrsMocks.processing),
      jaApiCalls.getCVRSfile(cvrsMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Setup')
      const fileTypeSelect = screen.getByLabelText(/CVR File Type:/)
      within(fileTypeSelect).getByRole('option', {
        name: 'Dominion',
        selected: true,
      })
      userEvent.selectOptions(
        fileTypeSelect,
        screen.getByRole('option', { name: 'ClearBallot' })
      )

      const cvrsInput = screen.getByLabelText('Select a file...')
      const cvrsButton = screen.getByRole('button', { name: 'Upload File' })

      userEvent.click(cvrsButton)
      await screen.findByText('You must upload a file')

      userEvent.upload(cvrsInput, cvrsFile)
      userEvent.click(cvrsButton)

      await screen.findByText('Uploading...')
      expect(fileTypeSelect).toBeDisabled()

      await screen.findByText('Processing...')
      expect(fileTypeSelect).toBeDisabled()

      await screen.findByText('Uploaded at 11/18/2020, 9:39:14 PM.')
      expect(fileTypeSelect).toBeDisabled()
      within(fileTypeSelect).getByRole('option', {
        name: 'ClearBallot',
        selected: true,
      })
      screen.getByText('Audit setup complete')
    })
  })

  it('after deleting CVRs, keeps last selected CVR file type ', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettingsMocks.ballotComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getCVRSfile(cvrsMocks.processed),
      jaApiCalls.deleteCVRs,
      jaApiCalls.getCVRSfile(cvrsMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Uploaded at 6/8/2020, 9:39:14 PM.')
      screen.getByRole('option', { name: 'ClearBallot', selected: true })
      userEvent.click(screen.getAllByRole('button', { name: 'Delete File' })[1])
      await screen.findByText('Select a file...')
      screen.getByRole('option', { name: 'ClearBallot', selected: true })
    })
  })

  it('displays errors on invalid CVRs upload', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettingsMocks.ballotComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getCVRSfile(cvrsMocks.processed),
      ...jaApiCalls.uploadCVRsCalls,
      jaApiCalls.getCVRSfile(cvrsMocks.errored),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Setup')
      expect(screen.getAllByText(/Uploaded/)).toHaveLength(2)

      // Replace & upload errored CVRs
      userEvent.click(
        screen.getAllByRole('button', {
          name: 'Replace File',
        })[1]
      )
      userEvent.upload(
        await screen.findByLabelText('Select a file...'),
        cvrsFile
      )
      userEvent.click(screen.getByRole('button', { name: 'Upload File' }))
      await screen.findByText('Invalid CSV')
    })
  })

  it('allows CVRs ZIP file to be uploaded for Hart', async () => {
    const cvrsZip = new File(['test cvr data'], 'cvrs.zip', {
      type: 'application/zip',
    })

    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettingsMocks.ballotComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getCVRSfile(cvrsMocks.empty),
      ...jaApiCalls.uploadCVRZipCalls,
      jaApiCalls.getCVRSfile(cvrsMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Setup')

      userEvent.selectOptions(
        screen.getByLabelText(/CVR File Type:/),
        screen.getByRole('option', { name: 'Hart' })
      )

      const fileSelect = screen.getByLabelText('Select a file...')
      userEvent.upload(fileSelect, cvrsZip)
      userEvent.click(screen.getByRole('button', { name: 'Upload File' }))
      await screen.findByText('Uploaded at 11/18/2020, 9:39:14 PM.')
    })
  })

  it('displays errors after reprocessing CVRs on replacing manifest', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettingsMocks.ballotComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
      jaApiCalls.getCVRSfile(cvrsMocks.processed),
      ...jaApiCalls.uploadManifestCalls,
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getCVRSfile(cvrsMocks.errored),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Setup')

      // Upload a new manifest
      userEvent.click(
        screen.getAllByRole('button', { name: 'Replace File' })[0]
      )
      userEvent.upload(
        await screen.findByLabelText('Select a file...'),
        manifestFile
      )
      userEvent.click(screen.getByRole('button', { name: 'Upload File' }))
      await screen.findByText(/Uploaded/)
      await screen.findByText('Invalid CSV')
    })
  })

  it('shows error with incorrect file', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettingsMocks.batchComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
      ...jaApiCalls.uploadManifestCalls,
      jaApiCalls.getBallotManifestFile(manifestMocks.errored),
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Setup')
      const [manifestInput, talliesInput] = screen.getAllByLabelText(
        'Select a file...'
      )
      const [manifestButton, talliesButton] = screen.getAllByRole('button', {
        name: 'Upload File',
      })

      expect(talliesInput).toBeDisabled()
      expect(talliesButton).toBeDisabled()

      userEvent.click(manifestButton)
      await screen.findByText('You must upload a file')

      userEvent.upload(manifestInput, manifestFile)
      userEvent.click(manifestButton)
      await screen.findByText('Invalid CSV')
    })
  })

  it('replaces manifest file', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettingsMocks.batchComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
      ...jaApiCalls.uploadManifestCalls,
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Setup')

      const replaceButton = await screen.findByText('Replace File')
      userEvent.click(replaceButton)
      const inputFiles = await screen.findAllByText('Select a file...')
      expect(inputFiles).toHaveLength(2)

      const [manifestInput] = screen.getAllByLabelText('Select a file...')
      const [manifestButton] = screen.getAllByRole('button', {
        name: 'Upload File',
      })

      userEvent.click(manifestButton)
      await screen.findByText('You must upload a file')

      userEvent.upload(manifestInput, manifestFile)
      userEvent.click(manifestButton)
      await screen.findByText('Current file:')
    })
  })

  it('stays on the file upload screen when sample is being drawn', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettingsMocks.all),
      jaApiCalls.getRounds(roundMocks.drawSampleInProgress),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Setup')
    })
  })

  it('stays on the file upload screen when drawing sample errors', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettingsMocks.all),
      jaApiCalls.getRounds(roundMocks.drawSampleErrored),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Setup')
    })
  })

  it('shows a link to batch inventory for enabled organizations', async () => {
    const expectedCalls = [
      {
        ...jaApiCalls.getUser,
        response: {
          user: {
            ...jaApiCalls.getUser.response.user,
            jurisdictions: [
              {
                ...jaApiCalls.getUser.response.user.jurisdictions[0],
                election: {
                  ...jaApiCalls.getUser.response.user.jurisdictions[0].election,
                  organizationId: 'a67791e3-90a0-4d4e-a5e7-929f82bf4ce6', // VotingWorks Internal Sandbox
                },
              },
            ],
          },
        },
      },
      jaApiCalls.getSettings(auditSettingsMocks.batchComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Setup')
      screen.getByRole('heading', { name: 'Batch Audit File Preparation Tool' })
      const button = screen.getByRole('button', {
        name: 'Go to Batch Audit File Preparation Tool',
      })
      expect(button).toHaveAttribute(
        'href',
        '/election/1/jurisdiction/jurisdiction-id-1/batch-inventory'
      )
    })
  })
})
