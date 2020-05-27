import React from 'react'
import { waitFor } from '@testing-library/react'
import { BrowserRouter as Router, useParams } from 'react-router-dom'
import SingleJurisdictionAudit from './index'
import { statusStates, dummyBallots } from './_mocks'
import * as utilities from '../utilities'
import { asyncActRender } from '../testUtilities'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()
const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)

checkAndToastMock.mockReturnValue(false)

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'), // use actual for all non-hook parts
  useRouteMatch: jest.fn(),
  useParams: jest.fn(),
}))
const paramsMock = useParams as jest.Mock
paramsMock.mockReturnValue({
  electionId: '1',
  view: 'setup',
})

afterEach(() => {
  apiMock.mockClear()
  checkAndToastMock.mockClear()
  paramsMock.mockReturnValue({
    electionId: '1',
    view: 'setup',
  })
})

describe('RiskLimitingAuditForm', () => {
  it('fetches initial state from api', async () => {
    apiMock.mockImplementation(async () => statusStates.empty)
    const { container } = await asyncActRender(
      <Router>
        <SingleJurisdictionAudit />
      </Router>
    )

    expect(container).toMatchSnapshot()
    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock.mock.calls[0][0]).toMatch(
        /\/election\/[^/]+\/audit\/status/
      )
      expect(apiMock.mock.results[0].value).resolves.toBe(statusStates.empty)
    })
  })

  it('renders correctly with initialData', async () => {
    const { container } = await asyncActRender(
      <Router>
        <SingleJurisdictionAudit />
      </Router>
    )
    expect(container).toMatchSnapshot()
  })

  it('still renders if there is a server error', async () => {
    checkAndToastMock.mockReturnValueOnce(true)
    await asyncActRender(
      <Router>
        <SingleJurisdictionAudit />
      </Router>
    )
    expect(checkAndToastMock).toBeCalledTimes(1)
  })

  it('does not render SelectBallotsToAudit when /audit/status is processing samplesizes', async () => {
    apiMock.mockImplementation(async () => statusStates.contestFirstRound)
    const { container, queryByTestId } = await asyncActRender(
      <Router>
        <SingleJurisdictionAudit />
      </Router>
    )

    expect(queryByTestId('form-two')).toBeNull()
    expect(container).toMatchSnapshot()
    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock.mock.calls[0][0]).toMatch(
        /\/election\/[^/]+\/audit\/status/
      )
      expect(apiMock.mock.results[0].value).resolves.toBe(
        statusStates.contestFirstRound
      )
    })
  })

  it('renders SelectBallotsToAudit when /audit/status returns contest data', async () => {
    apiMock.mockImplementation(async () => statusStates.sampleSizeOptions)
    const { container, findByTestId } = await asyncActRender(
      <Router>
        <SingleJurisdictionAudit />
      </Router>
    )

    await findByTestId('form-two')
    expect(container).toMatchSnapshot()
    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock.mock.calls[0][0]).toMatch(
        /\/election\/[^/]+\/audit\/status/
      )
      expect(apiMock.mock.results[0].value).resolves.toBe(
        statusStates.sampleSizeOptions
      )
    })
  })

  it('does not render CalculateRiskMeasurement when audit.jurisdictions has length but audit.rounds does not', async () => {
    apiMock.mockImplementation(async () => statusStates.jurisdictionsInitial)
    const { container, findByTestId, queryByTestId } = await asyncActRender(
      <Router>
        <SingleJurisdictionAudit />
      </Router>
    ) // this one will not have the first empty round

    await findByTestId('form-two')
    expect(queryByTestId('form-three-1')).toBeNull()
    expect(container).toMatchSnapshot()
    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock.mock.calls[0][0]).toMatch(
        /\/election\/[^/]+\/audit\/status/
      )
      expect(apiMock.mock.results[0].value).resolves.toBe(
        statusStates.jurisdictionsInitial
      )
    })
  })

  it('renders CalculateRiskMeasurement when /audit/status returns round data', async () => {
    apiMock
      .mockImplementationOnce(async () => statusStates.ballotManifestProcessed)
      .mockImplementationOnce(async () => dummyBallots)
    const { container, findByTestId } = await asyncActRender(
      <Router>
        <SingleJurisdictionAudit />
      </Router>
    ) // this one will not have the first empty round

    await findByTestId('form-three-1')
    expect(container).toMatchSnapshot()
    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(2)
      expect(apiMock.mock.calls[0][0]).toMatch(
        /\/election\/[^/]+\/audit\/status/
      )
      expect(apiMock.mock.results[0].value).resolves.toBe(
        statusStates.ballotManifestProcessed
      )
    })
  })
})
