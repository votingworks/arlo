import React from 'react'
import { render, fireEvent, wait } from '@testing-library/react'
import { toast } from 'react-toastify'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'
import { statusStates } from './_mocks'
import api from '../utilities'

const apiMock = api as jest.Mock<ReturnType<typeof api>, Parameters<typeof api>>

jest.mock('../utilities')

const setIsLoadingMock = jest.fn()
const updateAuditMock = jest.fn()

beforeEach(() => {
  setIsLoadingMock.mockReset()
  updateAuditMock.mockReset()
})

describe('CalculateRiskMeasurement', () => {
  it('renders first round correctly', () => {
    const container = render(
      <CalculateRiskMeasurement
        audit={statusStates[3]}
        isLoading={false}
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders completion in first round correctly', () => {
    const container = render(
      <CalculateRiskMeasurement
        audit={statusStates[4]}
        isLoading={false}
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders first round with loading correctly', () => {
    const container = render(
      <CalculateRiskMeasurement
        audit={statusStates[3]}
        isLoading
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders completion in first round with loading correctly', () => {
    const container = render(
      <CalculateRiskMeasurement
        audit={statusStates[4]}
        isLoading
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it(`handles inputs`, async () => {
    const toastSpy = jest.spyOn(toast, 'error').mockImplementation()
    apiMock.mockImplementation(() =>
      Promise.resolve({
        message: 'success',
        ok: true,
      })
    )
    const { container, getByTestId, queryAllByText, getByText } = render(
      <CalculateRiskMeasurement
        audit={statusStates[3]}
        isLoading={false}
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
      />
    )

    expect(container).toMatchSnapshot()

    const choiceOne = getByTestId(`round-0-contest-0-choice-choice-1`)
    const choiceTwo = getByTestId(`round-0-contest-0-choice-choice-2`)

    expect(choiceOne).toBeInstanceOf(HTMLInputElement)
    expect(choiceTwo).toBeInstanceOf(HTMLInputElement)

    if (
      choiceOne instanceof HTMLInputElement &&
      choiceTwo instanceof HTMLInputElement
    ) {
      fireEvent.change(choiceOne, { target: { value: -1 } })
      fireEvent.change(choiceTwo, { target: { value: -1 } })
      fireEvent.blur(choiceOne)
      fireEvent.blur(choiceTwo)
      expect(choiceOne.value).toBe('-1')
      expect(choiceTwo.value).toBe('-1')
      await wait(() => {
        expect(queryAllByText('Must be a positive number').length).toBe(2)
      })

      fireEvent.change(choiceOne, { target: { value: '0.5' } })
      fireEvent.change(choiceTwo, { target: { value: '0.5' } })
      fireEvent.blur(choiceOne)
      fireEvent.blur(choiceTwo)
      expect(choiceOne.value).toBe('0.5')
      expect(choiceTwo.value).toBe('0.5')
      await wait(() => {
        expect(queryAllByText('Must be an integer').length).toBe(2)
      })

      fireEvent.change(choiceOne, { target: { value: '' } })
      fireEvent.change(choiceTwo, { target: { value: '' } })
      fireEvent.blur(choiceOne)
      fireEvent.blur(choiceTwo)
      expect(choiceOne.value).toBe('')
      expect(choiceTwo.value).toBe('')
      await wait(() => {
        expect(queryAllByText('Must be a number').length).toBe(2)
      })

      fireEvent.change(choiceOne, { target: { value: '5' } })
      fireEvent.change(choiceTwo, { target: { value: '5' } })
      fireEvent.blur(choiceOne)
      fireEvent.blur(choiceTwo)
      expect(choiceOne.value).toBe('5')
      expect(choiceTwo.value).toBe('5')
      fireEvent.click(getByText('Calculate Risk Measurement'), {
        bubbles: true,
      })

      await wait(() => {
        expect(apiMock).toBeCalledTimes(1)
        expect(setIsLoadingMock).toBeCalledTimes(1)
        expect(updateAuditMock).toBeCalledTimes(1)
        expect(toastSpy).toBeCalledTimes(0)
      })
    }
  })

  it('downloads aggregated ballots report', () => {
    window.open = jest.fn()
    const { getByText } = render(
      <CalculateRiskMeasurement
        audit={statusStates[3]}
        isLoading={false}
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
      />
    )

    fireEvent.click(
      getByText('Download Aggregated Ballot Retrieval List for Round 1'),
      { bubbles: true }
    )

    expect(window.open).toHaveBeenCalledTimes(1)
    expect(window.open).toHaveBeenCalledWith(
      `/jurisdiction/jurisdiction-1/1/retrieval-list`
    )
  })

  it('downloads audit report', () => {
    window.open = jest.fn()
    const { getByText } = render(
      <CalculateRiskMeasurement
        audit={statusStates[4]}
        isLoading={false}
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
      />
    )

    fireEvent.click(getByText('Download Audit Report'), { bubbles: true })

    expect(window.open).toHaveBeenCalledTimes(1)
    expect(window.open).toHaveBeenCalledWith(`/audit/report`)
  })

  it('handles errors from api', async () => {
    apiMock.mockReset()
    apiMock.mockImplementation(() =>
      Promise.reject({
        message: 'error',
        ok: false,
      })
    )
    const toastSpy = jest.spyOn(toast, 'error').mockImplementation()
    const { getByTestId, getByText } = render(
      <CalculateRiskMeasurement
        audit={statusStates[3]}
        isLoading={false}
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
      />
    )

    const choiceOne: any = getByTestId(`round-0-contest-0-choice-choice-1`)
    const choiceTwo: any = getByTestId(`round-0-contest-0-choice-choice-2`)

    fireEvent.change(choiceOne, { target: { value: '5' } })
    fireEvent.change(choiceTwo, { target: { value: '5' } })
    fireEvent.click(getByText('Calculate Risk Measurement'), { bubbles: true })

    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(setIsLoadingMock).toBeCalledTimes(1)
      expect(updateAuditMock).toBeCalledTimes(0)
      expect(toastSpy).toBeCalledTimes(1)
    })
  })
})
