import React from 'react'
import { render, act } from '@testing-library/react'
import AuditForms from './RiskLimitingAuditForm'
import statusStates from './_mocks'
import api from '../utilities'

const apiMock = api as jest.Mock<ReturnType<typeof api>, Parameters<typeof api>>

jest.mock('../utilities')
apiMock
  .mockImplementationOnce(() => Promise.resolve(statusStates[0]))
  .mockImplementationOnce(() => Promise.resolve(statusStates[1]))
  .mockImplementationOnce(() => Promise.resolve(statusStates[2]))
  .mockImplementationOnce(() => Promise.resolve(statusStates[3]))

describe('RiskLimitingAuditForm', () => {
  it('renders correctly and fetches initial state from api', () => {
    let utils: any
    act(() => {
      utils = render(<AuditForms />)
    })
    const { container } = utils

    expect(container).toMatchSnapshot()
    expect(apiMock).toBeCalledTimes(1)
    expect(apiMock.mock.calls[0][0]).toBe('/audit/status')
  })

  it('renders SelectBallotsToAudit when /audit/status returns contest data', () => {
    let utils: any
    act(() => {
      utils = render(<AuditForms />)
    })
    const { container } = utils

    expect(container).toMatchSnapshot()
    expect(apiMock).toBeCalledTimes(2)
    expect(apiMock.mock.calls[1][0]).toBe('/audit/status')
  })

  it('does not render CalculateRiskMeasurement when audit.jurisdictions has length but audit.rounds does not', () => {
    let utils: any
    act(() => {
      utils = render(<AuditForms />) // this one will not have the first empty round
    })
    const { container } = utils

    expect(apiMock).toBeCalledTimes(3)
    expect(apiMock.mock.calls[0][0]).toBe('/audit/status')
    expect(container).toMatchSnapshot()
  })

  it('renders CalculateRiskMeasurement when /audit/status returns round data', () => {
    let utils: any
    act(() => {
      utils = render(<AuditForms />) // this one will not have the first empty round
    })
    const { container } = utils

    expect(apiMock).toBeCalledTimes(4)
    expect(apiMock.mock.calls[0][0]).toBe('/audit/status')
    expect(container).toMatchSnapshot()
  })
})
