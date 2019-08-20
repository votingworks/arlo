import React from 'react'
import {
  render,
  act,
  RenderResult,
  waitForElement,
} from '@testing-library/react'
import AuditForms from './RiskLimitingAuditForm'
import statusStates from './_mocks'
import api from '../utilities'

//const apiMock = api as jest.Mock<ReturnType<typeof api>, Parameters<typeof api>>
const apiMock = api as any

jest.mock('../utilities')

afterEach(() => {
  apiMock.mockClear()
})

describe('RiskLimitingAuditForm', () => {
  it('renders correctly and fetches initial state from api', () => {
    apiMock.mockReturnValue(statusStates[0])
    let utils: RenderResult
    act(() => {
      utils = render(<AuditForms />)
    })
    const { container } = utils!

    expect(apiMock.mock.results[0].value).toBe(statusStates[0])
    expect(container).toMatchSnapshot()
    expect(apiMock).toBeCalledTimes(1)
    expect(apiMock.mock.calls[0][0]).toBe('/audit/status')
  })

  it('renders SelectBallotsToAudit when /audit/status returns contest data', async () => {
    apiMock.mockReturnValue(statusStates[1])
    let utils: RenderResult
    act(() => {
      utils = render(<AuditForms />)
    })
    const { container, getByTestId } = utils!

    expect(apiMock.mock.results[0].value).toBe(statusStates[1])

    const formTwo = await waitForElement(() => {
      getByTestId('form-two')
    })

    expect(formTwo).toBeTruthy()
    expect(container).toMatchSnapshot()
    expect(apiMock).toBeCalledTimes(1)
    expect(apiMock.mock.calls[1][0]).toBe('/audit/status')
  })

  it('does not render CalculateRiskMeasurement when audit.jurisdictions has length but audit.rounds does not', async () => {
    apiMock.mockReturnValue(statusStates[2])
    let utils: RenderResult
    act(() => {
      utils = render(<AuditForms />) // this one will not have the first empty round
    })
    const { container, getByTestId, queryByTestId } = utils!

    expect(apiMock.mock.results[0].value).toBe(statusStates[2])

    const formTwo = await waitForElement(() => {
      getByTestId('form-two')
    })

    expect(apiMock).toBeCalledTimes(1)
    expect(formTwo).toBeTruthy()
    expect(queryByTestId('form-three-1')).toBeNull()
    expect(apiMock.mock.calls[0][0]).toBe('/audit/status')
    expect(container).toMatchSnapshot()
  })

  it('renders CalculateRiskMeasurement when /audit/status returns round data', async () => {
    apiMock.mockReturnValue(statusStates[3])
    let utils: RenderResult
    act(() => {
      utils = render(<AuditForms />) // this one will not have the first empty round
    })
    const { container, getByTestId } = utils!

    expect(apiMock.mock.results[0].value).toBe(statusStates[3])

    const formThree = await waitForElement(() => {
      getByTestId('form-three-1')
    })

    expect(apiMock).toBeCalledTimes(1)
    expect(formThree).toBeTruthy()
    expect(apiMock.mock.calls[0][0]).toBe('/audit/status')
    expect(container).toMatchSnapshot()
  })
})
