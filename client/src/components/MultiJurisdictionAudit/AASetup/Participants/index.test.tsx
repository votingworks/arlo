import React from 'react'
import { screen } from '@testing-library/react'
import { Route } from 'react-router-dom'
import userEvent from '@testing-library/user-event'
import relativeStages from '../_mocks'
import Participants from './index'
import jurisdictionFile from './_mocks'
import { auditSettings } from '../../useSetupMenuItems/_mocks'
import { renderWithRouter, withMockFetch } from '../../../testUtilities'
import { aaApiCalls } from '../../_mocks'
import { IFileInfo, FileProcessingStatus } from '../../useCSV'

const { nextStage } = relativeStages('participants')
const refreshMock = jest.fn()

const renderParticipants = () =>
  renderWithRouter(
    <Route path="/election/:electionId/setup">
      <Participants
        locked={false}
        nextStage={nextStage}
        refresh={refreshMock}
      />
    </Route>,
    { route: '/election/1/setup' }
  )

const fileMocks = {
  empty: { file: null, processing: null },
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
  beforeEach(() => {
    ;(nextStage.activate as jest.Mock).mockClear()
    refreshMock.mockClear()
  })

  it('submits participants file', async () => {
    const anotherFile = new File([], 'another file')
    const expectedCalls = [
      aaApiCalls.getSettings(auditSettings.blank),
      apiCalls.getJurisdictionsFile(fileMocks.empty),
      apiCalls.putJurisdictionsFile(jurisdictionFile),
      apiCalls.getJurisdictionsFile(fileMocks.processed),
      apiCalls.putJurisdictionsFile(anotherFile),
      apiCalls.getJurisdictionsFile(fileMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      nextStage.state = 'locked'

      renderParticipants()

      await screen.findByRole('heading', { name: 'Participants' })

      expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled()

      // Upload a file
      userEvent.upload(
        screen.getByLabelText('Select a CSV...'),
        jurisdictionFile
      )
      userEvent.click(screen.getByRole('button', { name: 'Upload File' }))

      await screen.findByText('Current file:')
      screen.getByText('file name')

      // Fake that setupMenuItems noticed the change and unlocked the next stage
      expect(refreshMock).toHaveBeenCalled()
      nextStage.state = 'live'

      // Replace the file in the input
      userEvent.click(screen.getByRole('button', { name: 'Replace File' }))
      userEvent.upload(screen.getByLabelText('Select a CSV...'), anotherFile)
      userEvent.click(screen.getByRole('button', { name: 'Upload File' }))
      await screen.findByText('Current file:')

      // Next button should be enabled now
      userEvent.click(screen.getByRole('button', { name: 'Next' }))
      expect(nextStage.activate).toHaveBeenCalled()
    })
  })

  it('submits participants and standardized contests file for ballot comparison audits', async () => {
    const contestsFile = new File([], 'contests file')
    const expectedCalls = [
      aaApiCalls.getSettings(auditSettings.blankBallotComparison),
      apiCalls.getJurisdictionsFile(fileMocks.empty),
      apiCalls.getStandardizedContestsFile(fileMocks.empty),
      apiCalls.putJurisdictionsFile(jurisdictionFile),
      apiCalls.getJurisdictionsFile(fileMocks.processed),
      apiCalls.putStandardizedContestsFile(contestsFile),
      apiCalls.getStandardizedContestsFile(fileMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderParticipants()

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
      ] = screen.getAllByLabelText('Select a CSV...')
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

      standardizedContestsFileInput = screen.getByLabelText('Select a CSV...')
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
      aaApiCalls.getSettings(auditSettings.blankBallotComparison),
      apiCalls.getJurisdictionsFile(fileMocks.errored),
      apiCalls.getStandardizedContestsFile(fileMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderParticipants()

      await screen.findByText('Current file:')
      screen.getByText('file name')
      screen.getByText('something went wrong')

      const standardizedContestsFileInput = screen.getByLabelText(
        'Select a CSV...'
      )
      const standardizedContestsFileUploadButton = screen.getByRole('button', {
        name: 'Upload File',
      })
      expect(standardizedContestsFileInput).toBeDisabled()
      expect(standardizedContestsFileUploadButton).toBeDisabled()
    })
  })
})
