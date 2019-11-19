import React from 'react'
import { render, fireEvent, wait } from '@testing-library/react'
import { toast } from 'react-toastify'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import { statusStates, ballotManifest } from './_mocks'
import { regexpEscape } from '../testUtilities'
import * as utilities from '../utilities'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()

const toastSpy = jest.spyOn(toast, 'error').mockImplementation()

async function inputAndSubmitForm() {
  const getStatusMock = jest
    .fn()
    .mockImplementationOnce(async () => statusStates[4]) // the POST to /election/{electionId}/audit/status after jurisdictions
  const updateAuditMock = jest
    .fn()
    .mockImplementationOnce(async () => statusStates[5]) // the POST to /election/{electionId}/audit/status after manifest

  const { getByLabelText, getByText } = render(
    <SelectBallotsToAudit
      audit={statusStates[2]}
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
  await wait(() => {
    expect(getByText('You must upload a manifest')).toBeTruthy()
  })
  fireEvent.change(manifestInput, { target: { files: [ballotManifest] } })

  const auditBoardInput: HTMLElement = getByLabelText(
    new RegExp(regexpEscape('Set the number of audit boards you wish to use.')),
    { selector: 'select' }
  )
  fireEvent.change(auditBoardInput, { target: { selected: 1 } })

  const sampleSizeInput = getByLabelText(
    '379 samples (80% chance of reaching risk limit and completing the audit in one round)'
  )
  fireEvent.click(sampleSizeInput, { bubbles: true })

  const submitButton = getByText('Select Ballots To Audit')
  fireEvent.click(submitButton, { bubbles: true })

  return [getStatusMock, updateAuditMock]
}

beforeEach(() => {
  apiMock.mockReset()
  toastSpy.mockReset()
})

describe('SelectBallotsToAudit', () => {
  it('renders correctly', () => {
    const { container, rerender } = render(
      <SelectBallotsToAudit
        audit={statusStates[1]}
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
        audit={statusStates[1]}
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
        audit={statusStates[2]}
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
      getByLabelText('BRAVO Average Sample Number: 269 samples').hasAttribute(
        'checked'
      )
    ).toBeTruthy()
  })

  it('conditionally shows custom text input and submits', async () => {
    const getStatusMock = jest
      .fn()
      .mockImplementationOnce(async () => statusStates[3]) // the POST to /election/{electionId}/audit/status after jurisdictions
    const updateAuditMock = jest
      .fn()
      .mockImplementationOnce(async () => statusStates[4]) // the POST to /election/{electionId}/audit/status after manifest

    const {
      getByText,
      queryAllByTestId,
      getByTestId,
      getByLabelText,
      queryAllByText,
    } = render(
      <SelectBallotsToAudit
        audit={statusStates[2]}
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
    await wait(() => {
      expect(queryAllByTestId('customSampleSize[contest-1]').length).toBe(1)
    })
    fireEvent.click(getByText('BRAVO Average Sample Number: 269 samples'), {
      bubbles: true,
    })
    await wait(() => {
      expect(queryAllByTestId('customSampleSize[contest-1]').length).toBe(0)
    })
    fireEvent.click(customRadio, { bubbles: true })
    await wait(async () => {
      const customInput = getByTestId('customSampleSize[contest-1]')
      fireEvent.change(customInput, { target: { value: '3000' } })
      fireEvent.blur(customInput)
      await wait(() => {
        expect(
          getByText('Must be less than or equal to the total number of ballots')
        ).toBeTruthy()
      })
      fireEvent.change(customInput, { target: { value: '11' } })
      fireEvent.blur(customInput)
      await wait(() => {
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

      await wait(() => {
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

        expect((getStatusMock as jest.Mock).mock.calls.length).toBe(1)
        expect((updateAuditMock as jest.Mock).mock.calls.length).toBe(1)
      })
    })
  })

  it('changes sampleSize based on audit.rounds.contests.sampleSize', () => {
    const { getByLabelText } = render(
      <SelectBallotsToAudit
        audit={statusStates[5]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )

    expect(
      getByLabelText(
        '379 samples (80% chance of reaching risk limit and completing the audit in one round)'
      ).hasAttribute('checked')
    ).toBeTruthy()
  })

  it('changes number of audits', () => {
    const { getByLabelText } = render(
      <SelectBallotsToAudit
        audit={statusStates[1]}
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
    }
  })

  it('submits sample size, ballot manifest, and number of audits', async () => {
    apiMock.mockImplementation(async () => ({}))

    const [getStatusMock, updateAuditMock] = await inputAndSubmitForm()

    await wait(() => {
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
                  name: 'Audit Board #1',
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

      expect((getStatusMock as jest.Mock).mock.calls.length).toBe(1)
      expect((updateAuditMock as jest.Mock).mock.calls.length).toBe(1)
    })
  })

  it('handles api error on /audit/sample-size', async () => {
    apiMock
      .mockImplementationOnce(() => Promise.reject({ message: 'error' }))
      .mockImplementation(async () => ({}))

    const [getStatusMock, updateAuditMock] = await inputAndSubmitForm()

    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(toastSpy).toBeCalledTimes(1)

      expect(getStatusMock).toBeCalledTimes(0)
      expect(updateAuditMock).toBeCalledTimes(0)
    })
  })

  it('handles api error on /audit/jurisdictions', async () => {
    apiMock
      .mockImplementationOnce(async () => ({}))
      .mockImplementationOnce(() => Promise.reject({ message: 'error' }))
      .mockImplementation(async () => ({}))

    const [getStatusMock, updateAuditMock] = await inputAndSubmitForm()

    await wait(() => {
      expect(apiMock).toBeCalledTimes(2)
      expect(toastSpy).toBeCalledTimes(1)

      expect(getStatusMock).toBeCalledTimes(0)
      expect(updateAuditMock).toBeCalledTimes(0)
    })
  })

  it('handles api error on /audit/jurisdiction/:id/manifest', async () => {
    apiMock
      .mockImplementationOnce(async () => ({}))
      .mockImplementationOnce(async () => ({}))
      .mockImplementationOnce(() => Promise.reject({ message: 'error' }))

    const [getStatusMock, updateAuditMock] = await inputAndSubmitForm()

    await wait(() => {
      expect(apiMock).toBeCalledTimes(3)
      expect(toastSpy).toBeCalledTimes(1)

      expect(getStatusMock).toBeCalledTimes(1)
      expect(updateAuditMock).toBeCalledTimes(0)
    })
  })

  it('uses the highest prob value from duplicate sampleSizes', () => {
    statusStates[1].rounds[0].contests[0].sampleSizeOptions = [
      { size: 30, prob: 0.8, type: null }, // eslint-disable-line no-null/no-null
      { size: 30, prob: 0.9, type: null }, // eslint-disable-line no-null/no-null
    ]
    const { queryAllByText } = render(
      <SelectBallotsToAudit
        audit={statusStates[1]}
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
    const statusState = { ...statusStates[1] }
    statusState.rounds[0].contests[0].sampleSizeOptions = [
      { size: 30, prob: null, type: null }, // eslint-disable-line no-null/no-null
      { size: 30, prob: null, type: null }, // eslint-disable-line no-null/no-null
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
