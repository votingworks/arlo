import React from 'react'
import { render, fireEvent, waitForDomChange } from '@testing-library/react'
import toastMock from 'react-toastify'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import { statusStates, ballotManifest } from './_mocks'
import apiMock from '../utilities'

jest.mock('../utilities')
jest.mock('react-toastify')

describe('SelectBallotsToAudit', () => {
  it('renders correctly', () => {
    const container = render(
      <SelectBallotsToAudit
        audit={statusStates[1]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
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
      />
    )

    expect(
      getByLabelText(
        '379 samples (80% chance of reaching risk limit and completing the audit in one round)'
      ).hasAttribute('checked')
    ).toBeTruthy()
  })

  it('changes number of audits', () => {
    const { getByTestId } = render(
      <SelectBallotsToAudit
        audit={statusStates[1]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
      />
    )

    const auditBoardInput: any = getByTestId('audit-boards')
    fireEvent.change(auditBoardInput, { target: { selected: 3 } })
    expect(auditBoardInput.selected).toBe(3)
  })

  it('submits sample size, ballot manifest, and number of audits', async () => {
    ;(apiMock as jest.Mock).mockImplementation(() => Promise.resolve())
    const getStatusMock = jest
      .fn()
      .mockImplementationOnce(() => Promise.resolve(statusStates[2])) // the POST to /audit/status after jurisdictions
    const updateAuditMock = jest
      .fn()
      .mockImplementationOnce(() => Promise.resolve(statusStates[3])) // the POST to /audit/status after manifest

    const {
      getByTestId,
      getByLabelText,
      getByText,
      queryAllByText,
      container,
    } = render(
      <SelectBallotsToAudit
        audit={statusStates[1]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
      />
    )

    const manifestInput = getByTestId('ballot-manifest')
    fireEvent.change(manifestInput, { target: { files: [ballotManifest] } })

    const auditBoardInput: any = getByTestId('audit-boards')
    fireEvent.change(auditBoardInput, { target: { selected: 1 } })

    const sampleSizeInput = getByLabelText(
      '379 samples (80% chance of reaching risk limit and completing the audit in one round)'
    )
    fireEvent.click(sampleSizeInput, { bubbles: true })

    const submitButton = getByText('Select Ballots To Audit')
    fireEvent.click(submitButton, { bubbles: true })

    waitForDomChange({ container }).then(
      () => {
        expect((apiMock as jest.Mock).mock.calls.length).toBe(3)

        expect((apiMock as jest.Mock).mock.calls[0][0]).toBe(
          '/audit/sample-size'
        )
        expect((apiMock as jest.Mock).mock.calls[0][1]).toMatchObject({
          method: 'POST',
          body: {
            size: 379,
          },
          headers: {
            'Content-Type': 'application/json',
          },
        })

        expect((apiMock as jest.Mock).mock.calls[1][0]).toBe(
          '/audit/jurisdictions'
        )
        expect((apiMock as jest.Mock).mock.calls[1][1]).toMatchObject({
          method: 'POST',
          body: {
            jurisdictions: [
              {
                id: 'jurisdiction-1',
                name: 'Jurisdiction 1',
                contests: ['contest-1'],
                auditBoards: {
                  id: 'audit-board-1',
                  name: 'Audit Board #1',
                  members: [],
                },
              },
            ],
          },
          headers: {
            'Content-Type': 'application/json',
          },
        })

        expect((apiMock as jest.Mock).mock.calls[2][0]).toBe(
          '/jurisdiction/jurisdiction-1/manifest'
        )

        expect((getStatusMock as jest.Mock).mock.calls.length).toBe(1)
        expect((updateAuditMock as jest.Mock).mock.calls.length).toBe(1)

        expect(queryAllByText('Select Ballots To Audit').length).toBe(0)
      },
      error => {
        throw new Error(error)
      }
    )
  })

  it('handles api error on /audit/sample-size', async () => {
    ;(apiMock as jest.Mock)
      .mockImplementationOnce(() => Promise.reject())
      .mockImplementation(() => Promise.resolve())
    const getStatusMock = jest
      .fn()
      .mockImplementationOnce(() => Promise.resolve(statusStates[2])) // the POST to /audit/status after jurisdictions
    const updateAuditMock = jest
      .fn()
      .mockImplementationOnce(() => Promise.resolve(statusStates[3])) // the POST to /audit/status after manifest

    const {
      getByTestId,
      getByLabelText,
      getByText,
      queryAllByText,
      container,
    } = render(
      <SelectBallotsToAudit
        audit={statusStates[1]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
      />
    )

    const manifestInput = getByTestId('ballot-manifest')
    fireEvent.change(manifestInput, { target: { files: [ballotManifest] } })

    const auditBoardInput: any = getByTestId('audit-boards')
    fireEvent.change(auditBoardInput, { target: { selected: 1 } })

    const sampleSizeInput = getByLabelText(
      '379 samples (80% chance of reaching risk limit and completing the audit in one round)'
    )
    fireEvent.click(sampleSizeInput, { bubbles: true })

    const submitButton = getByText('Select Ballots To Audit')
    fireEvent.click(submitButton, { bubbles: true })

    waitForDomChange({ container }).then(
      () => {
        expect(apiMock).toBeCalledTimes(3) // failure on /audit/sample-size doesn't block other calls
        expect(toastMock).toBeCalledTimes(1)

        expect(getStatusMock).toBeCalledTimes(1)
        expect(updateAuditMock).toBeCalledTimes(1)

        expect(queryAllByText('Select Ballots To Audit').length).toBe(0)
      },
      error => {
        throw new Error(error)
      }
    )
  })

  it('handles api error on /audit/jurisdictions', async () => {
    ;(apiMock as jest.Mock)
      .mockImplementationOnce(() => Promise.resolve())
      .mockImplementationOnce(() => Promise.reject())
      .mockImplementation(() => Promise.resolve())
    const getStatusMock = jest
      .fn()
      .mockImplementationOnce(() => Promise.resolve(statusStates[2])) // the POST to /audit/status after jurisdictions
    const updateAuditMock = jest
      .fn()
      .mockImplementationOnce(() => Promise.resolve(statusStates[3])) // the POST to /audit/status after manifest

    const {
      getByTestId,
      getByLabelText,
      getByText,
      queryAllByText,
      container,
    } = render(
      <SelectBallotsToAudit
        audit={statusStates[1]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
      />
    )

    const manifestInput = getByTestId('ballot-manifest')
    fireEvent.change(manifestInput, { target: { files: [ballotManifest] } })

    const auditBoardInput: any = getByTestId('audit-boards')
    fireEvent.change(auditBoardInput, { target: { selected: 1 } })

    const sampleSizeInput = getByLabelText(
      '379 samples (80% chance of reaching risk limit and completing the audit in one round)'
    )
    fireEvent.click(sampleSizeInput, { bubbles: true })

    const submitButton = getByText('Select Ballots To Audit')
    fireEvent.click(submitButton, { bubbles: true })

    waitForDomChange({ container }).then(
      () => {
        expect(apiMock).toBeCalledTimes(2)
        expect(toastMock).toBeCalledTimes(1)

        expect(getStatusMock).toBeCalledTimes(0)
        expect(updateAuditMock).toBeCalledTimes(0)

        expect(queryAllByText('Select Ballots To Audit').length).toBe(1)
      },
      error => {
        throw new Error(error)
      }
    )
  })

  it('handles api error on /audit/jurisdiction/:id/manifest', async () => {
    ;(apiMock as jest.Mock)
      .mockImplementationOnce(() => Promise.resolve())
      .mockImplementationOnce(() => Promise.resolve())
      .mockImplementationOnce(() => Promise.reject())
    const getStatusMock = jest
      .fn()
      .mockImplementationOnce(() => Promise.resolve(statusStates[2])) // the POST to /audit/status after jurisdictions
    const updateAuditMock = jest
      .fn()
      .mockImplementationOnce(() => Promise.resolve(statusStates[3])) // the POST to /audit/status after manifest

    const {
      getByTestId,
      getByLabelText,
      getByText,
      queryAllByText,
      container,
    } = render(
      <SelectBallotsToAudit
        audit={statusStates[1]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
      />
    )

    const manifestInput = getByTestId('ballot-manifest')
    fireEvent.change(manifestInput, { target: { files: [ballotManifest] } })

    const auditBoardInput: any = getByTestId('audit-boards')
    fireEvent.change(auditBoardInput, { target: { selected: 1 } })

    const sampleSizeInput = getByLabelText(
      '379 samples (80% chance of reaching risk limit and completing the audit in one round)'
    )
    fireEvent.click(sampleSizeInput, { bubbles: true })

    const submitButton = getByText('Select Ballots To Audit')
    fireEvent.click(submitButton, { bubbles: true })

    waitForDomChange({ container }).then(
      () => {
        expect(apiMock).toBeCalledTimes(3)
        expect(toastMock).toBeCalledTimes(1)

        expect(getStatusMock).toBeCalledTimes(1)
        expect(updateAuditMock).toBeCalledTimes(1)

        expect(queryAllByText('Select Ballots To Audit').length).toBe(1)
      },
      error => {
        throw new Error(error)
      }
    )
  })

  it('uses the highest prob value from duplicate sampleSizes', () => {
    statusStates[1].contests[0].sampleSizeOptions = [
      { size: 30, prob: 0.8 },
      { size: 30, prob: 0.9 },
    ]
    const { queryAllByText } = render(
      <SelectBallotsToAudit
        audit={statusStates[1]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
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
    statusState.contests[0].sampleSizeOptions = [{ size: 30 }, { size: 30 }]
    const { queryAllByText } = render(
      <SelectBallotsToAudit
        audit={statusState}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
      />
    )

    expect(queryAllByText('30 samples').length).toBe(1)
  })
})
