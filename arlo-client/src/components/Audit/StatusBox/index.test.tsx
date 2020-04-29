import React from 'react'
import { render, wait, fireEvent } from '@testing-library/react'
import * as utilities from '../../utilities'
import StatusBox from '.'
import { generateApiMock } from '../../testUtilities'
import { jurisdictionMocks, roundMocks } from './_mocks'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()

const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)

checkAndToastMock.mockReturnValue(false)

afterEach(() => {
  apiMock.mockClear()
  checkAndToastMock.mockClear()
})

describe('StatusBox', () => {
  it('renders initial message', () => {
    apiMock.mockImplementation(
      generateApiMock({
        roundReturn: roundMocks.none,
        jurisdictionReturn: jurisdictionMocks.none,
      })
    )
    const { container, queryByText } = render(
      <StatusBox electionId="1" refreshId="1" />
    )
    expect(queryByText('The audit has not started.')).toBeTruthy()
    expect(queryByText('Audit setup is not complete.')).toBeTruthy()
    expect(queryByText('No jurisdictions have been created yet.')).toBeTruthy()
    expect(queryByText('Download Audit Reports')).toBeFalsy()
    expect(queryByText('Start Round 1')).toBeFalsy()
    expect(container).toMatchSnapshot()
  })

  it('after jurisdictions are made with no uploads', async () => {
    apiMock.mockImplementation(
      generateApiMock({
        roundReturn: roundMocks.none,
        jurisdictionReturn: jurisdictionMocks.noUploads,
      })
    )
    const { container, queryByText } = render(
      <StatusBox electionId="1" refreshId="1" />
    )
    await wait(() => {
      expect(queryByText('The audit has not started.')).toBeTruthy()
      expect(queryByText('Audit setup is not complete.')).toBeTruthy()
      expect(queryByText('0 of 2 have completed file uploads.')).toBeTruthy()
      expect(queryByText('Download Audit Reports')).toBeFalsy()
      expect(queryByText('Start Round 1')).toBeFalsy()
      expect(container).toMatchSnapshot()
    })
  })

  it('after jurisdictions are made with partial uploads', async () => {
    apiMock.mockImplementation(
      generateApiMock({
        roundReturn: { rounds: [] },
        jurisdictionReturn: jurisdictionMocks.halfUploads,
      })
    )
    const { container, queryByText } = render(
      <StatusBox electionId="1" refreshId="1" />
    )
    await wait(() => {
      expect(queryByText('The audit has not started.')).toBeTruthy()
      expect(queryByText('Audit setup is not complete.')).toBeTruthy()
      expect(queryByText('1 of 2 have completed file uploads.')).toBeTruthy()
      expect(queryByText('Download Audit Reports')).toBeFalsy()
      expect(queryByText('Start Round 1')).toBeFalsy()
      expect(container).toMatchSnapshot()
    })
  })

  it('after round one is started', async () => {
    apiMock.mockImplementation(
      generateApiMock({
        roundReturn: roundMocks.firstRoundIncomplete,
        jurisdictionReturn: jurisdictionMocks.halfUploads,
      })
    )
    const { container, queryByText } = render(
      <StatusBox electionId="1" refreshId="1" />
    )
    await wait(() => {
      expect(queryByText('Round 1 of the audit is in progress.')).toBeTruthy()
      expect(queryByText('0 of 2 have completed Round 1')).toBeTruthy()
      expect(queryByText('Download Audit Reports')).toBeFalsy()
      expect(queryByText('Start Round 1')).toBeFalsy()
      expect(container).toMatchSnapshot()
    })
  })

  it('after round one is finished but another is needed', async () => {
    apiMock.mockImplementation(
      generateApiMock({
        roundReturn: roundMocks.firstRoundIncomplete,
        jurisdictionReturn: jurisdictionMocks.allFinishedFirstRound,
      })
    )
    const { container, queryByText } = render(
      <StatusBox electionId="1" refreshId="1" />
    )
    await wait(() => {
      expect(
        queryByText('Round 1 of the audit is complete - another round needed.')
      ).toBeTruthy()
      expect(queryByText('When you are ready, start Round 2')).toBeTruthy()
      expect(queryByText('Download Audit Reports')).toBeFalsy()
      expect(queryByText('Start Round 2')).toBeTruthy()
      expect(container).toMatchSnapshot()
    })
  })

  it('after completion of audit in first round', async () => {
    apiMock.mockImplementation(
      generateApiMock({
        roundReturn: roundMocks.firstRoundComplete,
        jurisdictionReturn: jurisdictionMocks.halfUploads,
      })
    )
    const { container, queryByText } = render(
      <StatusBox electionId="1" refreshId="1" />
    )
    await wait(() => {
      expect(queryByText('The audit is complete.')).toBeTruthy()
      expect(queryByText('Download Audit Reports')).toBeTruthy()
      expect(queryByText('Start Round 1')).toBeFalsy()
      expect(container).toMatchSnapshot()
    })
  })

  it('downloads audit report', async () => {
    window.open = jest.fn()
    apiMock.mockImplementation(
      generateApiMock({
        roundReturn: roundMocks.firstRoundComplete,
        jurisdictionReturn: jurisdictionMocks.halfUploads,
      })
    )
    const { getByText, queryByText } = render(
      <StatusBox electionId="1" refreshId="1" />
    )
    await wait(() => expect(queryByText('Download Audit Reports')).toBeTruthy())
    fireEvent.click(getByText('Download Audit Reports'), { bubbles: true })
    await wait(() => {
      expect(window.open).toBeCalledTimes(1)
      expect(window.open).toBeCalledWith('/election/1/audit/report')
    })
  })

  it('starts round two', async () => {
    apiMock
      .mockImplementationOnce(
        generateApiMock({
          roundReturn: roundMocks.firstRoundIncomplete,
          jurisdictionReturn: jurisdictionMocks.allFinishedFirstRound,
        })
      )
      .mockImplementationOnce(
        generateApiMock({
          roundReturn: roundMocks.firstRoundIncomplete,
          jurisdictionReturn: jurisdictionMocks.allFinishedFirstRound,
        })
      )
      .mockImplementation(generateApiMock({ roundReturn: { status: 'ok' } }))
    const { getByText, queryByText } = render(
      <StatusBox electionId="1" refreshId="1" />
    )
    await wait(() => {
      expect(
        queryByText('Round 1 of the audit is complete - another round needed.')
      ).toBeTruthy()
      expect(queryByText('When you are ready, start Round 2')).toBeTruthy()
      expect(queryByText('Download Audit Reports')).toBeFalsy()
      expect(queryByText('Start Round 2')).toBeTruthy()
    })
    fireEvent.click(getByText('Start Round 2'), { bubbles: true })
    await wait(() => {
      expect(apiMock).toHaveBeenCalledTimes(3)
      expect(apiMock.mock.calls[2][0]).toBe('/election/1/round')
      expect(apiMock.mock.calls[2][1]).toMatchObject({
        body: JSON.stringify({
          roundNum: 2,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
        method: 'POST',
      })
    })
  })
})
