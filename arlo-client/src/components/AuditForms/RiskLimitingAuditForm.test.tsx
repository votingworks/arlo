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

const apiMock = api as jest.Mock<ReturnType<typeof api>, Parameters<typeof api>>

jest.mock('../utilities')

describe('RiskLimitingAuditForm', () => {
  it('renders correctly and fetches initial state from api', () => {
    apiMock.mockImplementation(() => Promise.resolve(statusStates[0]))
    let utils: RenderResult
    act(() => {
      utils = render(<AuditForms />)
    })
    const { container } = utils!

    expect(container).toMatchSnapshot()
    expect(apiMock).toBeCalledTimes(1)
    expect(apiMock.mock.calls[0][0]).toBe('/audit/status')
  })

  it('renders SelectBallotsToAudit when /audit/status returns contest data', async () => {
    apiMock.mockImplementation(() => Promise.resolve(statusStates[1]))
    let utils: RenderResult
    //act(() => {
    utils = render(<AuditForms />)
    //})
    const { container, getByTestId } = utils!

    const formTwo = await waitForElement(() => {
      getByTestId('formTwo')
    })

    expect(container).toMatchSnapshot()
    expect(formTwo).toBeTruthy()
    expect(apiMock).toBeCalledTimes(1)
    expect(apiMock.mock.calls[1][0]).toBe('/audit/status')
  })

  it('does not render CalculateRiskMeasurement when audit.jurisdictions has length but audit.rounds does not', async () => {
    apiMock.mockImplementation(() => Promise.resolve(statusStates[2]))
    let utils: RenderResult
    //act(() => {
    utils = render(<AuditForms />) // this one will not have the first empty round
    //})
    const { container, getByTestId, queryByTestId } = utils!

    const formTwo = await waitForElement(() => {
      getByTestId('formTwo')
    })

    expect(apiMock).toBeCalledTimes(1)
    expect(formTwo).toBeTruthy()
    expect(queryByTestId('formThree-1')).toBeNull()
    expect(apiMock.mock.calls[0][0]).toBe('/audit/status')
    expect(container).toMatchSnapshot()
  })

  it('renders CalculateRiskMeasurement when /audit/status returns round data', async () => {
    apiMock.mockImplementation(() => Promise.resolve(statusStates[3]))
    let utils: RenderResult
    //act(() => {
    utils = render(<AuditForms />) // this one will not have the first empty round
    //})
    const { container, getByTestId } = utils!

    const formThree = await waitForElement(() => {
      getByTestId('formThree-1')
    })

    expect(apiMock).toBeCalledTimes(1)
    expect(formThree).toBeTruthy()
    expect(apiMock.mock.calls[0][0]).toBe('/audit/status')
    expect(container).toMatchSnapshot()
  })
})
