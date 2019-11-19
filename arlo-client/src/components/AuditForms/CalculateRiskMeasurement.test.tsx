import React from 'react'
import { render, fireEvent, wait } from '@testing-library/react'
import { toast } from 'react-toastify'
import jsPDF from 'jspdf'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'
import { statusStates, dummyBallots } from './_mocks'
import * as utilities from '../utilities'

jest.spyOn(HTMLCanvasElement.prototype, 'getContext').mockImplementation()

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()

jest.mock('jspdf')

const jspdfMock = jsPDF as jest.Mock

const setIsLoadingMock = jest.fn()
const updateAuditMock = jest.fn()
const getStatusMock = jest.fn().mockImplementation(async () => statusStates[5])
const toastSpy = jest.spyOn(toast, 'error').mockImplementation()

let jspdfInstance: any
beforeEach(() => {
  jspdfInstance = {
    addImage: jest.fn(),
    setFontSize: jest.fn(),
    addPage: jest.fn(),
    text: jest.fn(),
    splitTextToSize: jest.fn().mockReturnValue(['']),
    save: jest.fn(),
    autoPrint: jest.fn(),
  }
  jspdfMock.mockImplementation(() => jspdfInstance)
  setIsLoadingMock.mockClear()
  updateAuditMock.mockClear()
  getStatusMock.mockClear()
  toastSpy.mockClear()
  apiMock.mockClear()
  jspdfMock.mockClear()
})

describe('CalculateRiskMeasurement', () => {
  it('renders first round correctly', () => {
    const container = render(
      <CalculateRiskMeasurement
        audit={statusStates[4]}
        isLoading={false}
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders completion in first round correctly', () => {
    const container = render(
      <CalculateRiskMeasurement
        audit={statusStates[5]}
        isLoading={false}
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders first round with loading correctly', () => {
    const container = render(
      <CalculateRiskMeasurement
        audit={statusStates[4]}
        isLoading
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders completion in first round with loading correctly', () => {
    const container = render(
      <CalculateRiskMeasurement
        audit={statusStates[5]}
        isLoading
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()
  })

  it(`handles inputs`, async () => {
    apiMock.mockImplementation(async () => ({
      message: 'success',
      ok: true,
    }))
    const { container, getByLabelText, queryAllByText, getByText } = render(
      <CalculateRiskMeasurement
        audit={statusStates[4]}
        isLoading={false}
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )

    expect(container).toMatchSnapshot()

    const choiceOne = getByLabelText('choice one')
    const choiceTwo = getByLabelText('choice two')

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
        expect(setIsLoadingMock).toBeCalledTimes(2)
        expect(getStatusMock).toBeCalledTimes(1)
        expect(updateAuditMock).toBeCalledTimes(1)
        expect(toastSpy).toBeCalledTimes(0)
      })
    }
  })

  it(`handles background process timeout`, async () => {
    const dateIncrementor = (function*() {
      let i = 10
      while (true) {
        i += 130000
        yield i
      }
    })()
    const dateSpy = jest
      .spyOn(Date, 'now')
      .mockImplementation(() => dateIncrementor.next().value)

    apiMock.mockImplementation(async () => ({
      message: 'success',
      ok: true,
    }))

    const getStatusMock = jest
      .fn()
      .mockImplementation(async () => statusStates[6])

    const { getByText } = render(
      <CalculateRiskMeasurement
        audit={statusStates[4]}
        isLoading={false}
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )

    fireEvent.click(getByText('Calculate Risk Measurement'), {
      bubbles: true,
    })

    await wait(() => {
      expect(dateSpy).toBeCalled()
      expect(toastSpy).toBeCalledTimes(1)
      expect(apiMock).toBeCalled()
      expect(setIsLoadingMock).toBeCalledTimes(1)
      expect(getStatusMock).toBeCalled()
      expect(updateAuditMock).toBeCalledTimes(0)
    })
  })

  it('downloads labels sheets', async () => {
    apiMock.mockImplementationOnce(async () => dummyBallots)
    const { getByText } = render(
      <CalculateRiskMeasurement
        audit={statusStates[3]}
        isLoading={false}
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )

    fireEvent.click(getByText('Download Label Sheets for Round 1'), {
      bubbles: true,
    })

    await wait(() => {
      expect(apiMock).toHaveBeenCalledTimes(1)
      expect(jspdfMock).toHaveBeenCalledTimes(1)
    })
    expect(jspdfInstance.setFontSize).toHaveBeenCalledTimes(1)
    expect(jspdfInstance.splitTextToSize).toHaveBeenCalledTimes(80) // called twice per label, with 40 labels
    expect(jspdfInstance.text).toHaveBeenCalledTimes(120) // called thrice per label, with 40 labels
    expect(jspdfInstance.addPage).toHaveBeenCalledTimes(1) // 40 ballots have 40 labels, which requires two pages
    expect(jspdfInstance.save).toHaveBeenCalledTimes(1)
  })

  it('downloads placeholder sheets', async () => {
    apiMock.mockImplementationOnce(async () => dummyBallots)
    const { getByText } = render(
      <CalculateRiskMeasurement
        audit={statusStates[3]}
        isLoading={false}
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )

    fireEvent.click(getByText('Download Placeholders for Round 1'), {
      bubbles: true,
    })

    await wait(() => {
      expect(apiMock).toHaveBeenCalledTimes(1)
      expect(jspdfMock).toHaveBeenCalledTimes(1)
    })
    expect(jspdfInstance.setFontSize).toHaveBeenCalledTimes(1)
    expect(jspdfInstance.splitTextToSize).toHaveBeenCalledTimes(80) // called twice per label, with 40 labels
    expect(jspdfInstance.text).toHaveBeenCalledTimes(120) // called thrice per label, with 40 labels
    expect(jspdfInstance.addPage).toHaveBeenCalledTimes(39) // one page per placeholder, with 40 placeholders for 40 ballots
    expect(jspdfInstance.save).toHaveBeenCalledTimes(1)
  })

  it('downloads aggregated ballots report', () => {
    window.open = jest.fn()
    const { getByText } = render(
      <CalculateRiskMeasurement
        audit={statusStates[4]}
        isLoading={false}
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )

    fireEvent.click(
      getByText('Download Aggregated Ballot Retrieval List for Round 1'),
      { bubbles: true }
    )

    expect(window.open).toBeCalledTimes(1)
    expect(window.open).toBeCalledWith(
      `/election/1/jurisdiction/jurisdiction-1/1/retrieval-list`
    )
  })

  it('downloads audit report', () => {
    window.open = jest.fn()
    const { getByText } = render(
      <CalculateRiskMeasurement
        audit={statusStates[5]}
        isLoading={false}
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )

    fireEvent.click(getByText('Download Audit Report'), { bubbles: true })

    expect(window.open).toBeCalledTimes(1)
    expect(window.open).toBeCalledWith(`/election/1/audit/report`)
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
    const { getByLabelText, getByText } = render(
      <CalculateRiskMeasurement
        audit={statusStates[4]}
        isLoading={false}
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )

    const choiceOne = getByLabelText('choice one')
    const choiceTwo = getByLabelText('choice two')

    expect(choiceOne).toBeInstanceOf(HTMLInputElement)
    expect(choiceTwo).toBeInstanceOf(HTMLInputElement)

    if (
      choiceOne instanceof HTMLInputElement &&
      choiceTwo instanceof HTMLInputElement
    ) {
      fireEvent.change(choiceOne, { target: { value: '5' } })
      fireEvent.change(choiceTwo, { target: { value: '5' } })
      fireEvent.click(getByText('Calculate Risk Measurement'), {
        bubbles: true,
      })

      await wait(() => {
        expect(apiMock).toBeCalledTimes(1)
        expect(setIsLoadingMock).toBeCalledTimes(1)
        expect(updateAuditMock).toBeCalledTimes(0)
        expect(toastSpy).toBeCalledTimes(1)
      })
    }
  })
})
