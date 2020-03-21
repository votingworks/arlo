import React from 'react'
import { render, fireEvent, wait } from '@testing-library/react'
import { BrowserRouter as Router, useParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import { statusStates } from '../../_mocks'
import relativeStages from '../_mocks'
import Participants from './index'
import jurisdictionFile from './_mocks'
import * as utilities from '../../../utilities'

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

const formData: FormData = new FormData()
formData.append('jurisdictions', jurisdictionFile, jurisdictionFile.name)

const { nextStage } = relativeStages('Participants')

const fillAndSubmit = async () => {
  const {
    getByText,
    getByLabelText,
    queryByLabelText,
    queryByText,
    getByTestId,
  } = render(
    <Router>
      <Participants audit={statusStates[0]} nextStage={nextStage} />
    </Router>
  )

  fireEvent.change(getByTestId('state-field'), {
    target: { value: 'WA' },
  })

  const csvInput = getByLabelText('Select a CSV...')
  fireEvent.change(csvInput, { target: { files: [] } })
  fireEvent.blur(csvInput)
  await wait(() => expect(queryByText('You must upload a file')).toBeTruthy())
  fireEvent.change(csvInput, { target: { files: [jurisdictionFile] } })
  await wait(() => expect(queryByText('You must upload a file')).toBeFalsy())
  await wait(() => expect(queryByLabelText('Select a CSV...')).toBeFalsy())
  await wait(() => expect(queryByLabelText('jurisdictions.csv')).toBeTruthy())

  fireEvent.click(getByText('Submit & Next'), { bubbles: true })
}

beforeEach(() => {
  apiMock.mockClear()
  toastSpy.mockClear()
  checkAndToastMock.mockClear()
  routeMock.mockClear()
  ;(nextStage.activate as jest.Mock).mockClear()
})

describe('Audit Setup > Contests', () => {
  it('renders empty state correctly', () => {
    const { container } = render(
      <Router>
        <Participants audit={statusStates[0]} nextStage={nextStage} />
      </Router>
    )
    expect(container).toMatchSnapshot()
  })

  it('selects a state and submits it', async () => {
    await fillAndSubmit()
    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock).toHaveBeenNthCalledWith(
        1,
        expect.stringMatching(/\/election\/[^/]+\/jurisdictions\/file/),
        { body: formData, method: 'PUT' }
      )
      expect(nextStage.activate).toHaveBeenCalledTimes(1)
    })
  })

  it('handles api error on /election/:electionId/jurisdictions/file', async () => {
    apiMock.mockRejectedValue({ message: 'error' })

    await fillAndSubmit()

    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(toastSpy).toBeCalledTimes(1)
      expect(nextStage.activate).toHaveBeenCalledTimes(0)
    })
  })

  it('handles server error on /election/:electionId/jurisdictions/file', async () => {
    apiMock.mockResolvedValue(undefined)
    checkAndToastMock.mockReturnValue(true)

    await fillAndSubmit()

    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(toastSpy).toBeCalledTimes(0)
      expect(checkAndToastMock).toBeCalledTimes(1)
      expect(nextStage.activate).toHaveBeenCalledTimes(0)
    })
  })
})
