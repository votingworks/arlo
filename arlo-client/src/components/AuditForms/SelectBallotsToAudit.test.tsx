import React from 'react'
import { render, fireEvent, wait } from '@testing-library/react'
import { toast } from 'react-toastify'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import { statusStates, ballotManifest } from './_mocks'
import api from '../utilities'
import { regexpEscape } from '../testUtilities'

const apiMock = api as jest.Mock<ReturnType<typeof api>, Parameters<typeof api>>

jest.mock('../utilities')
const toastSpy = jest.spyOn(toast, 'error').mockImplementation()

async function inputAndSubmitForm() {
  const getStatusMock = jest
    .fn()
    .mockImplementationOnce(async () => statusStates[2]) // the POST to /audit/status after jurisdictions
  const updateAuditMock = jest
    .fn()
    .mockImplementationOnce(async () => statusStates[3]) // the POST to /audit/status after manifest

  const { getByLabelText, getByText } = render(
    <SelectBallotsToAudit
      audit={statusStates[1]}
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

  it('handles not having sample size options', () => {
    const statusState = {
      contests: [
        {
          choices: [
            {
              id: 'choice-1',
              name: 'choice one',
              numVotes: '792',
            },
            {
              id: 'choice-2',
              name: 'choice two',
              numVotes: '1325',
            },
          ],
          id: 'contest-1',
          name: 'contest name',
          totalBallotsCast: '2123',
          sampleSizeOptions: [],
        },
      ],
      jurisdictions: [],
      rounds: [],
      name: 'contest name',
      randomSeed: '123456789',
      riskLimit: '1',
    }
    const container = render(
      <SelectBallotsToAudit
        audit={statusState}
        isLoading={false}
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
        audit={statusStates[1]}
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
    expect(getByText('78 samples'))

    // correct default should be selected
    expect(
      getByLabelText('BRAVO Average Sample Number: 269 samples').hasAttribute(
        'checked'
      )
    ).toBeTruthy()
  })

  it('changes sampleSize based on audit.rounds.contests.sampleSize', () => {
    const { getByLabelText } = render(
      <SelectBallotsToAudit
        audit={statusStates[4]}
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

      expect(apiMock.mock.calls[0][0]).toBe('/audit/sample-size')
      expect(apiMock.mock.calls[0][1]).toMatchObject({
        method: 'POST',
        body: JSON.stringify({
          size: '379',
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })

      expect(apiMock.mock.calls[1][0]).toBe('/audit/jurisdictions')
      expect(JSON.parse(apiMock.mock.calls[1][1].body as string)).toMatchObject(
        {
          // TODO fix type
          jurisdictions: [
            {
              id: expect.stringMatching(/^[-0-9a-z]+$/),
              name: 'Jurisdiction 1',
              contests: ['contest-1'],
              auditBoards: [
                {
                  id: 'audit-board-1',
                  name: 'Audit Board #1',
                  members: [],
                },
              ],
            },
          ],
        }
      )

      expect(apiMock.mock.calls[2][0]).toBe(
        '/jurisdiction/jurisdiction-1/manifest'
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
    statusStates[1].contests[0].sampleSizeOptions = [
      { size: 30, prob: 0.8, type: null },
      { size: 30, prob: 0.9, type: null },
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
    statusState.contests[0].sampleSizeOptions = [
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
