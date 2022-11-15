import React from 'react'
import { screen, waitFor, render } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClientProvider } from 'react-query'
import Participants, { IParticipantsProps } from './Participants'
import { jurisdictionFile } from './_mocks'
import { withMockFetch, createQueryClient } from '../../../testUtilities'
import { IFileInfo, FileProcessingStatus } from '../../../useCSV'

jest.mock('axios')

const renderParticipants = (props: Partial<IParticipantsProps> = {}) => {
  const goToNextStage = jest.fn()
  return {
    goToNextStage,
    ...render(
      <QueryClientProvider client={createQueryClient()}>
        <Participants
          electionId="1"
          goToNextStage={goToNextStage}
          isStandardizedContestsFileEnabled={false}
          {...props}
        />
      </QueryClientProvider>
    ),
  }
}

const fileMocks = {
  empty: { file: null, processing: null },
  processing: {
    file: {
      name: 'file name',
      uploadedAt: '2020-12-03T23:10:14.024+00:00',
    },
    processing: {
      status: FileProcessingStatus.PROCESSING,
      error: null,
      startedAt: '2020-12-03T23:10:14.024+00:00',
      completedAt: null,
    },
  },
  processed: {
    file: {
      name: 'file name',
      uploadedAt: '2020-12-03T23:10:14.024+00:00',
    },
    processing: {
      status: FileProcessingStatus.PROCESSED,
      error: null,
      startedAt: '2020-12-03T23:10:14.024+00:00',
      completedAt: '2020-12-03T23:10:14.024+00:00',
    },
  },
  errored: {
    file: {
      name: 'file name',
      uploadedAt: '2020-12-03T23:10:14.024+00:00',
    },
    processing: {
      status: FileProcessingStatus.ERRORED,
      error: 'something went wrong',
      startedAt: '2020-12-03T23:10:14.024+00:00',
      completedAt: '2020-12-03T23:10:14.024+00:00',
    },
  },
}

const apiCalls = {
  getJurisdictionsFile: (response: IFileInfo) => ({
    url: '/api/election/1/jurisdiction/file',
    response,
  }),
  getStandardizedContestsFile: (response: IFileInfo) => ({
    url: '/api/election/1/standardized-contests/file',
    response,
  }),
  putJurisdictionsFile: (file: File) => {
    const formData: FormData = new FormData()
    formData.append('jurisdictions', file, file.name)
    return {
      url: '/api/election/1/jurisdiction/file',
      options: {
        method: 'PUT',
        body: formData,
      },
      response: { status: 'ok' },
    }
  },
  putStandardizedContestsFile: (file: File) => {
    const formData: FormData = new FormData()
    formData.append('standardized-contests', file, file.name)
    return {
      url: '/api/election/1/standardized-contests/file',
      options: {
        method: 'PUT',
        body: formData,
      },
      response: { status: 'ok' },
    }
  },
}

describe('Audit Setup > Participants', () => {
  it('heading should be participants & contests for ballot comparison', async () => {
    const expectedCalls = [
      apiCalls.getJurisdictionsFile(fileMocks.empty),
      apiCalls.getStandardizedContestsFile(fileMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderParticipants({ isStandardizedContestsFileEnabled: true })
      await screen.findByRole('heading', { name: 'Participants & Contests' })
    })
  })

  it('submits participants file', async () => {
    const anotherFile = new File([], 'another file')
    const expectedCalls = [
      apiCalls.getJurisdictionsFile(fileMocks.empty),
      apiCalls.putJurisdictionsFile(jurisdictionFile),
      apiCalls.getJurisdictionsFile(fileMocks.processed),
      apiCalls.putJurisdictionsFile(anotherFile),
      apiCalls.getJurisdictionsFile(fileMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { goToNextStage } = renderParticipants()

      await screen.findByRole('heading', { name: 'Participants' })

      expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled()

      // Upload a file
      userEvent.upload(
        screen.getByLabelText('Select a file...'),
        jurisdictionFile
      )
      userEvent.click(screen.getByRole('button', { name: 'Upload File' }))

      await screen.findByText('Current file:')
      screen.getByText('file name')

      // Replace the file in the input
      userEvent.click(screen.getByRole('button', { name: 'Replace File' }))
      userEvent.upload(screen.getByLabelText('Select a file...'), anotherFile)
      userEvent.click(screen.getByRole('button', { name: 'Upload File' }))
      await screen.findByText('Current file:')

      // Next button should be enabled now
      userEvent.click(screen.getByRole('button', { name: 'Next' }))
      expect(goToNextStage).toHaveBeenCalled()
    })
  })

  it('submits participants and standardized contests file for ballot comparison audits', async () => {
    const contestsFile = new File([], 'contests file')
    const expectedCalls = [
      apiCalls.getJurisdictionsFile(fileMocks.empty),
      apiCalls.getStandardizedContestsFile(fileMocks.empty),
      apiCalls.putJurisdictionsFile(jurisdictionFile),
      apiCalls.getJurisdictionsFile(fileMocks.processed),
      apiCalls.getStandardizedContestsFile(fileMocks.empty),
      apiCalls.putStandardizedContestsFile(contestsFile),
      apiCalls.getStandardizedContestsFile(fileMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderParticipants({ isStandardizedContestsFileEnabled: true })

      await screen.findByRole('heading', {
        name: 'Participating Jurisdictions',
      })
      await screen.findByRole('heading', {
        name: 'Standardized Contests',
      })
      let [
        // eslint-disable-next-line prefer-const
        jurisdictionsFileInput,
        standardizedContestsFileInput,
      ] = screen.getAllByLabelText('Select a file...')
      let [
        // eslint-disable-next-line prefer-const
        jurisdictionsFileUploadButton,
        standardizedContestsFileUploadButton,
      ] = screen.getAllByRole('button', { name: 'Upload File' })

      expect(standardizedContestsFileInput).toBeDisabled()
      expect(standardizedContestsFileUploadButton).toBeDisabled()

      // Upload jurisdictions file
      userEvent.upload(jurisdictionsFileInput, jurisdictionFile)
      userEvent.click(jurisdictionsFileUploadButton)

      await screen.findByText('Current file:')
      screen.getByText('file name')

      standardizedContestsFileInput = screen.getByLabelText('Select a file...')
      standardizedContestsFileUploadButton = screen.getByRole('button', {
        name: 'Upload File',
      })
      expect(standardizedContestsFileInput).toBeEnabled()
      expect(standardizedContestsFileUploadButton).toBeEnabled()

      // Upload standardized contests file
      userEvent.upload(standardizedContestsFileInput, contestsFile)
      userEvent.click(standardizedContestsFileUploadButton)

      await screen.findByText('contests file')
    })
  })

  it('submits participants and standardized contests file for hybrid audits', async () => {
    const contestsFile = new File([], 'contests file')
    const expectedCalls = [
      apiCalls.getJurisdictionsFile(fileMocks.empty),
      apiCalls.getStandardizedContestsFile(fileMocks.empty),
      apiCalls.putJurisdictionsFile(jurisdictionFile),
      apiCalls.getJurisdictionsFile(fileMocks.processed),
      apiCalls.getStandardizedContestsFile(fileMocks.empty),
      apiCalls.putStandardizedContestsFile(contestsFile),
      apiCalls.getStandardizedContestsFile(fileMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderParticipants({ isStandardizedContestsFileEnabled: true })

      await screen.findByRole('heading', {
        name: 'Participating Jurisdictions',
      })
      await screen.findByRole('heading', {
        name: 'Standardized Contests',
      })
      let [
        // eslint-disable-next-line prefer-const
        jurisdictionsFileInput,
        standardizedContestsFileInput,
      ] = screen.getAllByLabelText('Select a file...')
      let [
        // eslint-disable-next-line prefer-const
        jurisdictionsFileUploadButton,
        standardizedContestsFileUploadButton,
      ] = screen.getAllByRole('button', { name: 'Upload File' })

      expect(standardizedContestsFileInput).toBeDisabled()
      expect(standardizedContestsFileUploadButton).toBeDisabled()

      // Upload jurisdictions file
      userEvent.upload(jurisdictionsFileInput, jurisdictionFile)
      userEvent.click(jurisdictionsFileUploadButton)

      await screen.findByText('Current file:')
      screen.getByText('file name')

      standardizedContestsFileInput = screen.getByLabelText('Select a file...')
      standardizedContestsFileUploadButton = screen.getByRole('button', {
        name: 'Upload File',
      })
      expect(standardizedContestsFileInput).toBeEnabled()
      expect(standardizedContestsFileUploadButton).toBeEnabled()

      // Upload standardized contests file
      userEvent.upload(standardizedContestsFileInput, contestsFile)
      userEvent.click(standardizedContestsFileUploadButton)

      await screen.findByText('contests file')
    })
  })

  it('displays errors', async () => {
    const expectedCalls = [
      apiCalls.getJurisdictionsFile(fileMocks.errored),
      apiCalls.getStandardizedContestsFile(fileMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderParticipants({ isStandardizedContestsFileEnabled: true })

      await screen.findByText('Current file:')
      screen.getByText('file name')
      screen.getByText('something went wrong')

      const standardizedContestsFileInput = screen.getByLabelText(
        'Select a file...'
      )
      const standardizedContestsFileUploadButton = screen.getByRole('button', {
        name: 'Upload File',
      })
      expect(standardizedContestsFileInput).toBeDisabled()
      expect(standardizedContestsFileUploadButton).toBeDisabled()
    })
  })

  it('displays errors - hybrid', async () => {
    const expectedCalls = [
      apiCalls.getJurisdictionsFile(fileMocks.errored),
      apiCalls.getStandardizedContestsFile(fileMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderParticipants({ isStandardizedContestsFileEnabled: true })

      await screen.findByText('Current file:')
      screen.getByText('file name')
      screen.getByText('something went wrong')

      const standardizedContestsFileInput = screen.getByLabelText(
        'Select a file...'
      )
      const standardizedContestsFileUploadButton = screen.getByRole('button', {
        name: 'Upload File',
      })
      expect(standardizedContestsFileInput).toBeDisabled()
      expect(standardizedContestsFileUploadButton).toBeDisabled()
    })
  })

  it('do not show standardized contests for ballot polling', async () => {
    const expectedCalls = [apiCalls.getJurisdictionsFile(fileMocks.empty)]
    await withMockFetch(expectedCalls, async () => {
      renderParticipants()

      await screen.findByRole('heading', {
        name: 'Participants',
      })

      await waitFor(() =>
        expect(
          screen.queryByRole('heading', { name: 'Standardized Contests' })
        ).not.toBeInTheDocument()
      )
    })
  })

  it('displays errors on replacing standardized contests with invalid upload', async () => {
    const contestsFile = new File([], 'contests file')
    const expectedCalls = [
      apiCalls.getJurisdictionsFile(fileMocks.processed),
      apiCalls.getStandardizedContestsFile(fileMocks.processed),
      apiCalls.putStandardizedContestsFile(contestsFile),
      apiCalls.getStandardizedContestsFile(fileMocks.processing),
      apiCalls.getStandardizedContestsFile(fileMocks.errored),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderParticipants({ isStandardizedContestsFileEnabled: true })
      expect(await screen.findAllByText(/Uploaded/)).toHaveLength(2)

      // Replace & upload errored standardized contests
      userEvent.click(
        screen.getAllByRole('button', {
          name: 'Replace File',
        })[1]
      )
      userEvent.upload(
        await screen.findByLabelText('Select a file...'),
        contestsFile
      )
      userEvent.click(screen.getByRole('button', { name: 'Upload File' }))
      await screen.findByText(/Uploaded/)
      await screen.findByText('something went wrong', undefined, {
        timeout: 2000,
      })
    })
  })

  it('displays errors after reprocessing standardized contests', async () => {
    const expectedCalls = [
      apiCalls.getJurisdictionsFile(fileMocks.processed),
      apiCalls.getStandardizedContestsFile(fileMocks.processed),
      apiCalls.putJurisdictionsFile(jurisdictionFile),
      apiCalls.getJurisdictionsFile(fileMocks.processing),
      apiCalls.getJurisdictionsFile(fileMocks.processed),
      apiCalls.getStandardizedContestsFile(fileMocks.errored),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderParticipants({ isStandardizedContestsFileEnabled: true })
      expect(await screen.findAllByText(/Uploaded/)).toHaveLength(2)

      // Upload a new jurisdictions file
      userEvent.click(
        screen.getAllByRole('button', { name: 'Replace File' })[0]
      )
      userEvent.upload(
        screen.getByLabelText('Select a file...'),
        jurisdictionFile
      )
      userEvent.click(screen.getByRole('button', { name: 'Upload File' }))

      await screen.findByText(/Uploaded/)
      await screen.findByText('something went wrong', undefined, {
        timeout: 2000,
      })
    })
  })
})
