import React from 'react'
import {
  render,
  act,
  RenderResult,
  waitForElement,
  wait,
} from '@testing-library/react'
import AuditForms from './RiskLimitingAuditForm'
import statusStates from './_mocks'
import api from '../utilities'

const apiMock = api as jest.Mock<ReturnType<typeof api>, Parameters<typeof api>>

jest.mock('../utilities')

afterEach(() => {
  apiMock.mockClear()
})

describe('RiskLimitingAuditForm', () => {
  it('fetches initial state from api', async () => {
    apiMock.mockImplementation(() => Promise.resolve(statusStates[0]))
    let utils: RenderResult
    act(() => {
      utils = render(<AuditForms />)
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
      utils = render(<AuditForms />)
    })
    const { container } = utils!
    expect(container).toMatchSnapshot()
  })

  it('renders SelectBallotsToAudit when /audit/status returns contest data', async () => {
    apiMock.mockImplementation(() => Promise.resolve(statusStates[1]))
    let utils: RenderResult
    act(() => {
      utils = render(<AuditForms />)
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
      expect(apiMock.mock.results[0].value).resolves.toBe(statusStates[1])
    })
  })

  it('does not render CalculateRiskMeasurement when audit.jurisdictions has length but audit.rounds does not', async () => {
    apiMock.mockImplementation(() => Promise.resolve(statusStates[2]))
    let utils: RenderResult
    act(() => {
      utils = render(<AuditForms />) // this one will not have the first empty round
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
      expect(apiMock.mock.results[0].value).resolves.toBe(statusStates[2])
    })
  })

  it('renders CalculateRiskMeasurement when /audit/status returns round data', async () => {
    apiMock.mockImplementation(() => Promise.resolve(statusStates[3]))
    let utils: RenderResult
    act(() => {
      utils = render(<AuditForms />) // this one will not have the first empty round
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
      expect(apiMock.mock.results[0].value).resolves.toBe(statusStates[3])
    })
  })
})
