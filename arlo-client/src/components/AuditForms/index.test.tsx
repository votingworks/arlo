import React from 'react'
import {
  render,
  act,
  RenderResult,
  waitForElement,
  wait,
} from '@testing-library/react'
import AuditForms from './index'
import { statusStates } from './_mocks'
import { api } from '../utilities'
import { routerTestProps } from '../testUtilities'

const apiMock = api as jest.Mock<ReturnType<typeof api>, Parameters<typeof api>>

jest.mock('../utilities')

const routeProps = routerTestProps('/election/:electionId', { electionId: '1' })

afterEach(() => {
  apiMock.mockClear()
})

describe('RiskLimitingAuditForm', () => {
  it('fetches initial state from api', async () => {
    apiMock.mockImplementation(async () => statusStates[0])
    let utils: RenderResult
    act(() => {
      utils = render(<AuditForms {...routeProps} />)
    })
    const { container } = utils!

    expect(container).toMatchSnapshot()
    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock.mock.calls[0][0]).toBe('/audit/status')
      expect(apiMock.mock.results[0].value).resolves.toBe(statusStates[0])
    })
  })

  it('renders correctly with initialData', () => {
    let utils: RenderResult
    act(() => {
      utils = render(<AuditForms {...routeProps} />)
    })
    const { container } = utils!
    expect(container).toMatchSnapshot()
  })

  it('does not render SelectBallotsToAudit when /audit/status is processing samplesizes', async () => {
    apiMock.mockImplementation(async () => statusStates[1])
    let utils: RenderResult
    act(() => {
      utils = render(<AuditForms {...routeProps} />)
    })
    const { container, queryByTestId } = utils!

    expect(queryByTestId('form-two')).toBeNull()
    expect(container).toMatchSnapshot()
    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock.mock.calls[0][0]).toBe('/audit/status')
      expect(apiMock.mock.results[0].value).resolves.toBe(statusStates[1])
    })
  })

  it('renders SelectBallotsToAudit when /audit/status returns contest data', async () => {
    apiMock.mockImplementation(async () => statusStates[2])
    let utils: RenderResult
    act(() => {
      utils = render(<AuditForms {...routeProps} />)
    })
    const { container, getByTestId } = utils!

    const formTwo = await waitForElement(() => getByTestId('form-two'), {
      container,
    })

    expect(formTwo).toBeTruthy()
    expect(container).toMatchSnapshot()
    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock.mock.calls[0][0]).toBe('/audit/status')
      expect(apiMock.mock.results[0].value).resolves.toBe(statusStates[2])
    })
  })

  it('does not render CalculateRiskMeasurement when audit.jurisdictions has length but audit.rounds does not', async () => {
    apiMock.mockImplementation(async () => statusStates[3])
    let utils: RenderResult
    act(() => {
      utils = render(<AuditForms {...routeProps} />) // this one will not have the first empty round
    })
    const { container, getByTestId, queryByTestId } = utils!

    const formTwo = await waitForElement(() => getByTestId('form-two'), {
      container,
    })

    expect(formTwo).toBeTruthy()
    expect(queryByTestId('form-three-1')).toBeNull()
    expect(container).toMatchSnapshot()
    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock.mock.calls[0][0]).toBe('/audit/status')
      expect(apiMock.mock.results[0].value).resolves.toBe(statusStates[3])
    })
  })

  it('renders CalculateRiskMeasurement when /audit/status returns round data', async () => {
    apiMock.mockImplementation(async () => statusStates[4])
    let utils: RenderResult
    act(() => {
      utils = render(<AuditForms {...routeProps} />) // this one will not have the first empty round
    })
    const { container, getByTestId } = utils!

    const formThree = await waitForElement(() => getByTestId('form-three-1'), {
      container,
    })

    expect(formThree).toBeTruthy()
    expect(container).toMatchSnapshot()
    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock.mock.calls[0][0]).toBe('/audit/status')
      expect(apiMock.mock.results[0].value).resolves.toBe(statusStates[4])
    })
  })
})
