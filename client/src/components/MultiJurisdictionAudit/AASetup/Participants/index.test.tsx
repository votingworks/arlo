import React from 'react'
import { fireEvent, waitFor, render, screen } from '@testing-library/react'
import { BrowserRouter as Router, useParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import relativeStages from '../_mocks'
import Participants from './index'
import jurisdictionFile from './_mocks'
import * as utilities from '../../../utilities'
import useAuditSettings from '../../useAuditSettings'
import { fileProcessingMocks } from '../../useSetupMenuItems/_mocks'

const auditSettingsMock = useAuditSettings as jest.Mock

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()

const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)
const toastSpy = jest.spyOn(toast, 'error').mockImplementation()

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'), // use actual for all non-hook parts
  useParams: jest.fn(),
}))
const routeMock = useParams as jest.Mock
routeMock.mockReturnValue({
  electionId: '1',
  view: 'setup',
})

jest.mock('../../useAuditSettings')
auditSettingsMock.mockReturnValue([
  {
    state: null,
    electionName: null,
    online: null,
    randomSeed: null,
    riskLimit: null,
  },
  async () => true,
])

const formData: FormData = new FormData()
formData.append('jurisdictions', jurisdictionFile, jurisdictionFile.name)

const { nextStage } = relativeStages('participants')

const fillAndSubmit = async () => {
  render(
    <Router>
      <Participants locked={false} nextStage={nextStage} />
    </Router>
  )

  const csvInput = await screen.findByLabelText('Select a CSV...')
  fireEvent.change(csvInput, { target: { files: [] } })
  fireEvent.blur(csvInput)
  await waitFor(() =>
    expect(screen.queryByText('You must upload a file')).toBeTruthy()
  )
  fireEvent.change(csvInput, { target: { files: [jurisdictionFile] } })
  await waitFor(() =>
    expect(screen.queryByText('You must upload a file')).toBeFalsy()
  )
  await waitFor(() =>
    expect(screen.queryByLabelText('Select a CSV...')).toBeFalsy()
  )
  await waitFor(() =>
    expect(screen.queryByLabelText('jurisdictions.csv')).toBeTruthy()
  )

  fireEvent.click(screen.getByText('Save & Next'), { bubbles: true })
}

beforeEach(() => {
  apiMock.mockClear()
  toastSpy.mockClear()
  checkAndToastMock.mockClear()
  routeMock.mockClear()
  ;(nextStage.activate as jest.Mock).mockClear()
  auditSettingsMock.mockClear()
})

describe('Audit Setup > Participants', () => {
  beforeEach(() => {
    apiMock.mockImplementation(async (endpoint: string) => {
      switch (endpoint) {
        case '/election/1/jurisdiction/file':
          return { file: null, processing: null }
        default:
          return null
      }
    })
  })

  it('renders empty state correctly', async () => {
    const { container } = render(
      <Router>
        <Participants locked={false} nextStage={nextStage} />
      </Router>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    expect(container).toMatchSnapshot()
  })

  it('renders filled state correctly & resets file', async () => {
    apiMock.mockImplementation(async (endpoint: string) => {
      switch (endpoint) {
        case '/election/1/jurisdiction/file':
          return {
            file: {
              name: 'filename.csv',
              uploadedAt: '2019-07-18T16:34:07.000Z',
            },
            processing: fileProcessingMocks,
          }
        default:
          return null
      }
    })
    const { container } = render(
      <Router>
        <Participants locked={false} nextStage={nextStage} />
      </Router>
    )
    const resetButton = await screen.findByText('Replace File')
    expect(container).toMatchSnapshot()
    fireEvent.click(resetButton, { bubbles: true })
    await screen.findByLabelText('Select a CSV...')
    expect(container).toMatchSnapshot()
  })

  it('submits', async () => {
    apiMock
      .mockResolvedValueOnce({ file: null, processing: null })
      .mockResolvedValue({ status: 'ok' })
    await fillAndSubmit()
    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(3)
      expect(apiMock).toHaveBeenNthCalledWith(
        2,
        expect.stringMatching(/\/election\/[^/]+\/jurisdiction\/file/),
        { body: formData, method: 'PUT' }
      )
      expect(nextStage.activate).toHaveBeenCalledTimes(1)
    })
  })

  it.skip('handles api error on /election/:electionId/jurisdiction/file', async () => {
    // TEST TODO
    apiMock
      .mockResolvedValueOnce({ file: null, processing: null })
      .mockRejectedValue({ message: 'error' })

    await fillAndSubmit()

    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(2)
      expect(toastSpy).toBeCalledTimes(1)
      expect(nextStage.activate).toHaveBeenCalledTimes(0)
    })
  })
})
