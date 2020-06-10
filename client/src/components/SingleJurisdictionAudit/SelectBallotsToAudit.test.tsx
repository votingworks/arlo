import React from 'react'
import { render, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter as Router } from 'react-router-dom'
import { toast } from 'react-toastify'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import { statusStates, ballotManifest } from './_mocks'
import { regexpEscape } from '../testUtilities'
import * as utilities from '../utilities'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()

const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)
const toastSpy = jest.spyOn(toast, 'error').mockImplementation()

async function inputAndSubmitForm() {
  const getStatusMock = jest
    .fn()
    .mockImplementationOnce(async () => statusStates.ballotManifestProcessed) // the POST to /election/{electionId}/audit/status after jurisdictions
    .mockImplementation(async () => statusStates.completeInFirstRound) // the POST to /election/{electionId}/audit/status after manifest
  const updateAuditMock = jest
    .fn()
    .mockImplementationOnce(async () => statusStates.completeInFirstRound) // the POST to /election/{electionId}/audit/status after manifest

  const { getByLabelText, getByText } = render(
    <SelectBallotsToAudit
      audit={statusStates.sampleSizeOptions}
      isLoading={false}
      setIsLoading={jest.fn()}
      updateAudit={updateAuditMock}
      getStatus={getStatusMock}
      electionId="1"
    />
  )

  const manifestInput = getByLabelText('Select manifest...')
  fireEvent.change(manifestInput, { target: { files: [] } })
  fireEvent.blur(manifestInput)
  await waitFor(() => {
    expect(getByText('You must upload a manifest')).toBeTruthy()
  })
  fireEvent.change(manifestInput, { target: { files: [ballotManifest] } })

  const auditBoardInput: HTMLElement = getByLabelText(
    new RegExp(regexpEscape('Set the number of audit boards you wish to use.')),
    { selector: 'select' }
  )
  fireEvent.change(auditBoardInput, { target: { selectedIndex: 1 } })

  // const boardOneNameInput: HTMLElement = getByTestId('audit-name-0')
  // fireEvent.change(boardOneNameInput, { target: { value: 'Board One' } }) // removed until custom audit board name feature is added again

  const sampleSizeInput = getByLabelText(
    '379 samples (80% chance of reaching risk limit and completing the audit in one round)'
  )
  fireEvent.click(sampleSizeInput, { bubbles: true })

  const submitButton = getByText('Select Ballots To Audit')
  fireEvent.click(submitButton, { bubbles: true })

  return [getStatusMock, updateAuditMock]
}

beforeEach(() => {
  apiMock.mockClear()
  toastSpy.mockClear()
  checkAndToastMock.mockClear()
})

describe('SelectBallotsToAudit', () => {
  it('renders correctly', () => {
    const { container, rerender } = render(
      <SelectBallotsToAudit
        audit={statusStates.contestFirstRound}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()

    rerender(
      <SelectBallotsToAudit
        audit={statusStates.contestFirstRound}
        isLoading
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('has radio for selecting sampleSize', () => {
    const { getByText, getByLabelText } = render(
      <SelectBallotsToAudit
        audit={statusStates.sampleSizeOptions}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )

    // all options should be present
    expect(getByText('BRAVO Average Sample Number: 269 samples')).toBeTruthy()
    expect(
      getByText(
        '379 samples (80% chance of reaching risk limit and completing the audit in one round)'
      )
    ).toBeTruthy()
    expect(getByText('78 samples')).toBeTruthy()
    expect(
      getByText('Enter your own sample size (not recommended)')
    ).toBeTruthy()

    // correct default should be selected
    expect(
      getByLabelText('BRAVO Average Sample Number: 269 samples')
    ).toBeChecked()
  })

  it('conditionally shows custom text input and submits', async () => {
    const getStatusMock = jest
      .fn()
      .mockImplementationOnce(async () => statusStates.jurisdictionsInitial) // the POST to /election/{electionId}/audit/status after jurisdictions
      .mockImplementation(async () => statusStates.ballotManifestProcessed) // the POST to /election/{electionId}/audit/status after manifest
    const updateAuditMock = jest
      .fn()
      .mockImplementationOnce(async () => statusStates.ballotManifestProcessed) // the POST to /election/{electionId}/audit/status after manifest
    apiMock.mockImplementation(async () => {})

    const {
      getByText,
      queryAllByTestId,
      getByTestId,
      getByLabelText,
      queryAllByText,
    } = render(
      <SelectBallotsToAudit
        audit={statusStates.sampleSizeOptions}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )

    expect(queryAllByTestId('customSampleSize[contest-1]').length).toBe(0)
    const customRadio = getByText(
      'Enter your own sample size (not recommended)'
    )
    fireEvent.click(customRadio, { bubbles: true })
    await waitFor(() => {
      expect(queryAllByTestId('customSampleSize[contest-1]').length).toBe(1)
    })
    fireEvent.click(getByText('BRAVO Average Sample Number: 269 samples'), {
      bubbles: true,
    })
    await waitFor(() => {
      expect(queryAllByTestId('customSampleSize[contest-1]').length).toBe(0)
    })
    fireEvent.click(customRadio, { bubbles: true })
    await waitFor(() => {
      expect(queryAllByTestId('customSampleSize[contest-1]').length).toBe(1)
    })

    const customInput = getByTestId('customSampleSize[contest-1]')
    fireEvent.change(customInput, { target: { value: '3000' } })
    fireEvent.blur(customInput)
    await waitFor(() => {
      expect(
        getByText('Must be less than or equal to the total number of ballots')
      ).toBeTruthy()
    })
    fireEvent.change(customInput, { target: { value: '11' } })
    fireEvent.blur(customInput)
    await waitFor(() => {
      expect(
        queryAllByText(
          'Must be less than or equal to the total number of ballots'
        ).length
      ).toBe(0)
    })

    const manifestInput = getByLabelText('Select manifest...')
    fireEvent.change(manifestInput, { target: { files: [ballotManifest] } })

    const submitButton = getByText('Select Ballots To Audit')
    fireEvent.click(submitButton, { bubbles: true })

    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(3)

      expect(apiMock.mock.calls[0][0]).toMatch(
        /\/election\/[^/]+\/audit\/sample-size/
      )
      expect(apiMock.mock.calls[0][1]).toMatchObject({
        method: 'POST',
        body: JSON.stringify({
          size: '11',
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })

      expect(getStatusMock).toBeCalledTimes(2)
      expect(updateAuditMock).toBeCalledTimes(1)
      expect(checkAndToastMock).toBeCalledTimes(3)
    })
  })

  it('bails if the manifest failed to start processing', async () => {
    const getStatusMock = jest
      .fn()
      .mockImplementation(async () => statusStates.jurisdictionsInitial) // the POST to /election/{electionId}/audit/status after jurisdictions
    const updateAuditMock = jest
      .fn()
      .mockImplementationOnce(async () => statusStates.ballotManifestProcessed) // the POST to /election/{electionId}/audit/status after manifest
    apiMock.mockImplementation(async () => {})

    const { getByText, getByLabelText } = render(
      <SelectBallotsToAudit
        audit={statusStates.sampleSizeOptions}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )

    const manifestInput = getByLabelText('Select manifest...')
    fireEvent.change(manifestInput, { target: { files: [ballotManifest] } })

    const submitButton = getByText('Select Ballots To Audit')
    fireEvent.click(submitButton, { bubbles: true })

    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(3)

      expect(getStatusMock).toBeCalledTimes(2)
      expect(updateAuditMock).toBeCalledTimes(0)
      expect(checkAndToastMock).toBeCalledTimes(3)
    })
  })

  it('does not bail if the manifest processing errors', async () => {
    const getStatusMock = jest
      .fn()
      .mockImplementation(async () => statusStates.ballotManifestProcessError) // the POST to /election/{electionId}/audit/status after jurisdictions
    const updateAuditMock = jest
      .fn()
      .mockImplementationOnce(async () => statusStates.ballotManifestProcessed) // the POST to /election/{electionId}/audit/status after manifest
    apiMock.mockImplementation(async () => {})

    const { getByText, getByLabelText } = render(
      <SelectBallotsToAudit
        audit={statusStates.sampleSizeOptions}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )

    const manifestInput = getByLabelText('Select manifest...')
    fireEvent.change(manifestInput, { target: { files: [ballotManifest] } })

    const submitButton = getByText('Select Ballots To Audit')
    fireEvent.click(submitButton, { bubbles: true })

    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(3)

      expect(getStatusMock).toBeCalledTimes(2)
      expect(updateAuditMock).toBeCalledTimes(1)
      expect(checkAndToastMock).toBeCalledTimes(3)
    })
  })

  it('handles server timeout on ballot manifest processing', async () => {
    const dateIncrementor = (function* incr() {
      let i = 10
      while (true) {
        i += 130000
        yield i
      }
    })()
    const dateSpy = jest
      .spyOn(Date, 'now')
      .mockImplementation(() => dateIncrementor.next().value)

    const getStatusMock = jest
      .fn()
      .mockImplementation(async () => statusStates.jurisdictionsInitial) // the POST to /election/{electionId}/audit/status after jurisdictions
    const updateAuditMock = jest
      .fn()
      .mockImplementationOnce(async () => statusStates.ballotManifestProcessed) // the POST to /election/{electionId}/audit/status after manifest
    apiMock.mockImplementation(async () => {})

    const { getByText, getByLabelText } = render(
      <SelectBallotsToAudit
        audit={statusStates.sampleSizeOptions}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )

    const manifestInput = getByLabelText('Select manifest...')
    fireEvent.change(manifestInput, { target: { files: [ballotManifest] } })

    const submitButton = getByText('Select Ballots To Audit')
    fireEvent.click(submitButton, { bubbles: true })

    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(3)
      expect(dateSpy).toBeCalled()
      expect(updateAuditMock).toBeCalledTimes(0)
      expect(toastSpy).toBeCalledTimes(1)
      expect(getStatusMock).toBeCalledTimes(2)
      expect(checkAndToastMock).toBeCalledTimes(3)
    })
  })

  it('changes sampleSize based on audit.rounds.contests.sampleSize', () => {
    const { getByLabelText } = render(
      <Router>
        <SelectBallotsToAudit
          audit={statusStates.completeInFirstRound}
          isLoading={false}
          setIsLoading={jest.fn()}
          updateAudit={jest.fn()}
          getStatus={jest.fn()}
          electionId="1"
        />
      </Router>
    )

    expect(
      getByLabelText(
        '379 samples (80% chance of reaching risk limit and completing the audit in one round)'
      )
    ).toBeChecked()
  })

  it('changes number of audits', () => {
    const { getByLabelText, container } = render(
      <SelectBallotsToAudit
        audit={statusStates.contestFirstRound}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )

    const auditBoardInput = getByLabelText(
      new RegExp(
        regexpEscape('Set the number of audit boards you wish to use.')
      ),
      { selector: 'select' }
    )
    expect(auditBoardInput).toBeInstanceOf(HTMLSelectElement)
    if (auditBoardInput instanceof HTMLSelectElement) {
      fireEvent.change(auditBoardInput, { target: { selectedIndex: 2 } })
      expect(auditBoardInput.selectedOptions[0].innerHTML).toBe('3')
      expect(container).toMatchSnapshot()
      fireEvent.change(auditBoardInput, { target: { selectedIndex: 1 } })
      expect(container).toMatchSnapshot()
    }
  })

  it('submits sample size, ballot manifest, and audits', async () => {
    apiMock.mockImplementation(async () => {})

    const [getStatusMock, updateAuditMock] = await inputAndSubmitForm()

    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(3)

      expect(apiMock.mock.calls[0]).toMatchObject([
        expect.stringMatching(/\/election\/[^/]+\/audit\/sample-size/),
        {
          method: 'POST',
          body: JSON.stringify({
            size: '379',
          }),
          headers: {
            'Content-Type': 'application/json',
          },
        },
      ])

      {
        const [url, options] = apiMock.mock.calls[1]
        const body = options && JSON.parse(options.body as string)

        expect(url).toMatch(/\/election\/[^/]+\/audit\/jurisdictions/)
        expect(body).toMatchObject({
          // TODO fix type
          jurisdictions: [
            {
              id: expect.stringMatching(/^[-0-9a-z]+$/),
              name: 'Jurisdiction 1',
              contests: ['contest-1'],
              auditBoards: [
                {
                  id: expect.stringMatching(/^[-0-9a-z]+$/),
                  name: 'Audit Board #1', // change to 'Board One' if custom audit board feature is added back again
                  members: [],
                },
                {
                  id: expect.stringMatching(/^[-0-9a-z]+$/),
                  name: 'Audit Board #2',
                  members: [],
                },
              ],
            },
          ],
        })
      }

      expect(apiMock.mock.calls[2][0]).toMatch(
        /\/election\/[^/]+\/jurisdiction\/jurisdiction-1\/manifest/
      )

      expect(getStatusMock).toBeCalledTimes(2)
      expect(updateAuditMock).toBeCalledTimes(1)
    })
  })

  it('handles api error on /audit/sample-size', async () => {
    apiMock
      .mockRejectedValueOnce({ message: 'error' })
      .mockImplementation(async () => ({}))

    const [getStatusMock, updateAuditMock] = await inputAndSubmitForm()

    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(toastSpy).toBeCalledTimes(1)

      expect(getStatusMock).toBeCalledTimes(0)
      expect(updateAuditMock).toBeCalledTimes(0)
    })
  })

  it('handles api error on /audit/jurisdictions', async () => {
    apiMock
      .mockResolvedValueOnce(undefined)
      .mockRejectedValueOnce({ message: 'error' })
      .mockResolvedValue(undefined)

    const [getStatusMock, updateAuditMock] = await inputAndSubmitForm()

    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(2)
      expect(toastSpy).toBeCalledTimes(1)

      expect(getStatusMock).toBeCalledTimes(0)
      expect(updateAuditMock).toBeCalledTimes(0)
    })
  })

  it('handles api error on /audit/jurisdiction/:id/manifest', async () => {
    apiMock
      .mockResolvedValueOnce(undefined)
      .mockResolvedValueOnce(undefined)
      .mockRejectedValueOnce({ message: 'error' })

    const [getStatusMock, updateAuditMock] = await inputAndSubmitForm()

    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(3)
      expect(toastSpy).toBeCalledTimes(1)

      expect(getStatusMock).toBeCalledTimes(1)
      expect(updateAuditMock).toBeCalledTimes(0)
    })
  })

  it('handles server error on /audit/sample-size', async () => {
    apiMock.mockResolvedValue(undefined)
    checkAndToastMock.mockReturnValueOnce(true).mockReturnValue(false)

    const [getStatusMock, updateAuditMock] = await inputAndSubmitForm()

    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(toastSpy).toBeCalledTimes(0)
      expect(checkAndToastMock).toBeCalledTimes(1)
      expect(getStatusMock).toBeCalledTimes(0)
      expect(updateAuditMock).toBeCalledTimes(0)
    })
  })

  it('handles server error on /audit/jurisdictions', async () => {
    apiMock.mockResolvedValue(undefined)
    checkAndToastMock
      .mockReturnValueOnce(false)
      .mockReturnValueOnce(true)
      .mockReturnValue(false)

    const [getStatusMock, updateAuditMock] = await inputAndSubmitForm()

    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(2)
      expect(toastSpy).toBeCalledTimes(0)
      expect(checkAndToastMock).toBeCalledTimes(2)
      expect(getStatusMock).toBeCalledTimes(0)
      expect(updateAuditMock).toBeCalledTimes(0)
    })
  })

  it('handles server error on /audit/jurisdiction/:id/manifest', async () => {
    apiMock.mockResolvedValue(undefined)
    checkAndToastMock
      .mockReturnValueOnce(false)
      .mockReturnValueOnce(false)
      .mockReturnValueOnce(true)
      .mockReturnValue(false)

    const [getStatusMock, updateAuditMock] = await inputAndSubmitForm()

    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(3)
      expect(toastSpy).toBeCalledTimes(0)
      expect(checkAndToastMock).toBeCalledTimes(3)
      expect(getStatusMock).toBeCalledTimes(1)
      expect(updateAuditMock).toBeCalledTimes(0)
    })
  })

  it('uses the highest prob value from duplicate sampleSizes', () => {
    statusStates.contestFirstRound.rounds[0].contests[0].sampleSizeOptions = [
      { size: 30, prob: 0.8, type: null },
      { size: 30, prob: 0.9, type: null },
    ]
    const { queryAllByText } = render(
      <SelectBallotsToAudit
        audit={statusStates.contestFirstRound}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )

    expect(
      queryAllByText(
        '30 samples (90% chance of reaching risk limit and completing the audit in one round)'
      ).length
    ).toBe(1)
  })

  it('does not display duplicate sampleSize options', () => {
    const statusState = { ...statusStates.contestFirstRound }
    statusState.rounds[0].contests[0].sampleSizeOptions = [
      { size: 30, prob: null, type: null },
      { size: 30, prob: null, type: null },
    ]
    const { queryAllByText } = render(
      <SelectBallotsToAudit
        audit={statusState}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )

    expect(queryAllByText('30 samples').length).toBe(1)
  })
})
