import React from 'react'
import { render, fireEvent, waitFor } from '@testing-library/react'
import { toast } from 'react-toastify'
import jsPDF from 'jspdf'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'
import { statusStates, dummyBallots, incompleteDummyBallots } from './_mocks'
import * as utilities from '../utilities'

statusStates.jurisdictionsInitial.online = false
statusStates.ballotManifestProcessed.online = false
statusStates.completeInFirstRound.online = false
statusStates.firstRoundSampleSizeOptionsNull.online = false
statusStates.firstRoundSampleSizeOptions.online = false

jest.spyOn(HTMLCanvasElement.prototype, 'getContext').mockImplementation()

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()
const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)

jest.mock('jspdf')

const jspdfMock = jsPDF as jest.Mock

const sharedSetIsLoadingMock = jest.fn()
const sharedUpdateAuditMock = jest.fn()
const sharedGetStatusMock = jest
  .fn()
  .mockImplementation(async () => statusStates.completeInFirstRound)
const sharedToastSpy = jest.spyOn(toast, 'error').mockImplementation()

let jspdfInstance: jsPDF
beforeEach(() => {
  jspdfInstance = ({
    addImage: jest.fn(),
    setFontSize: jest.fn(),
    setFontStyle: jest.fn(),
    addPage: jest.fn(),
    text: jest.fn(),
    splitTextToSize: jest.fn().mockReturnValue(['']),
    save: jest.fn(),
    autoPrint: jest.fn(),
  } as unknown) as jsPDF
  jspdfMock.mockImplementation(() => jspdfInstance)
  sharedSetIsLoadingMock.mockClear()
  sharedUpdateAuditMock.mockClear()
  sharedGetStatusMock.mockClear()
  sharedToastSpy.mockClear()
  apiMock.mockClear()
  jspdfMock.mockClear()
  checkAndToastMock.mockClear()
})

describe('CalculateRiskMeasurement', () => {
  it('renders first round correctly', () => {
    const container = render(
      <CalculateRiskMeasurement
        audit={statusStates.ballotManifestProcessed}
        isLoading={false}
        setIsLoading={sharedSetIsLoadingMock}
        updateAudit={sharedUpdateAuditMock}
        getStatus={sharedGetStatusMock}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders completion in first round correctly', () => {
    const container = render(
      <CalculateRiskMeasurement
        audit={statusStates.completeInFirstRound}
        isLoading={false}
        setIsLoading={sharedSetIsLoadingMock}
        updateAudit={sharedUpdateAuditMock}
        getStatus={sharedGetStatusMock}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders first round with loading correctly', () => {
    const container = render(
      <CalculateRiskMeasurement
        audit={statusStates.ballotManifestProcessed}
        isLoading
        setIsLoading={sharedSetIsLoadingMock}
        updateAudit={sharedUpdateAuditMock}
        getStatus={sharedGetStatusMock}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders completion in first round with loading correctly', () => {
    const container = render(
      <CalculateRiskMeasurement
        audit={statusStates.completeInFirstRound}
        isLoading
        setIsLoading={sharedSetIsLoadingMock}
        updateAudit={sharedUpdateAuditMock}
        getStatus={sharedGetStatusMock}
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
        audit={statusStates.ballotManifestProcessed}
        isLoading={false}
        setIsLoading={sharedSetIsLoadingMock}
        updateAudit={sharedUpdateAuditMock}
        getStatus={sharedGetStatusMock}
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
      await waitFor(() => {
        expect(queryAllByText('Must be a positive number').length).toBe(2)
      })

      fireEvent.change(choiceOne, { target: { value: '0.5' } })
      fireEvent.change(choiceTwo, { target: { value: '0.5' } })
      fireEvent.blur(choiceOne)
      fireEvent.blur(choiceTwo)
      expect(choiceOne.value).toBe('0.5')
      expect(choiceTwo.value).toBe('0.5')
      await waitFor(() => {
        expect(queryAllByText('Must be an integer').length).toBe(2)
      })

      fireEvent.change(choiceOne, { target: { value: '' } })
      fireEvent.change(choiceTwo, { target: { value: '' } })
      fireEvent.blur(choiceOne)
      fireEvent.blur(choiceTwo)
      expect(choiceOne.value).toBe('')
      expect(choiceTwo.value).toBe('')
      await waitFor(() => {
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

      await waitFor(() => {
        expect(apiMock).toBeCalledTimes(1)
        expect(sharedSetIsLoadingMock).toBeCalledTimes(2)
        expect(sharedGetStatusMock).toBeCalledTimes(1)
        expect(sharedUpdateAuditMock).toBeCalledTimes(1)
        expect(sharedToastSpy).toBeCalledTimes(0)
      })
    }
  })

  it(`handles background process timeout`, async () => {
    const dateIncrementor = (function* incr() {
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
      .mockImplementation(
        async () => statusStates.firstRoundSampleSizeOptionsNull
      )

    const { getByText } = render(
      <CalculateRiskMeasurement
        audit={statusStates.ballotManifestProcessed}
        isLoading={false}
        setIsLoading={sharedSetIsLoadingMock}
        updateAudit={sharedUpdateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )

    fireEvent.click(getByText('Calculate Risk Measurement'), {
      bubbles: true,
    })

    await waitFor(() => {
      expect(dateSpy).toBeCalled()
      expect(sharedToastSpy).toBeCalledTimes(1)
      expect(apiMock).toBeCalled()
      expect(sharedSetIsLoadingMock).toBeCalledTimes(1)
      expect(getStatusMock).toBeCalled()
      expect(sharedUpdateAuditMock).toBeCalledTimes(0)
    })
  })

  it(`handles server errors`, async () => {
    apiMock.mockImplementation(async () => ({
      message: 'success',
      ok: true,
    }))
    checkAndToastMock
      .mockReturnValueOnce(true)
      .mockReturnValueOnce(true)
      .mockReturnValueOnce(true)

    const getStatusMock = jest
      .fn()
      .mockImplementation(
        async () => statusStates.firstRoundSampleSizeOptionsNull
      )

    const { getByText } = render(
      <CalculateRiskMeasurement
        audit={statusStates.ballotManifestProcessed}
        isLoading={false}
        setIsLoading={sharedSetIsLoadingMock}
        updateAudit={sharedUpdateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )

    fireEvent.click(getByText('Calculate Risk Measurement'), {
      bubbles: true,
    })

    await waitFor(() => {
      expect(checkAndToastMock).toBeCalledTimes(1)
      expect(sharedToastSpy).toBeCalledTimes(0)
      expect(apiMock).toBeCalled()
      expect(sharedSetIsLoadingMock).toBeCalledTimes(2)
      expect(getStatusMock).toBeCalledTimes(0)
      expect(sharedUpdateAuditMock).toBeCalledTimes(0)
    })

    fireEvent.click(getByText('Download Label Sheets for Round 1'), {
      bubbles: true,
    })

    fireEvent.click(getByText('Download Placeholders for Round 1'), {
      bubbles: true,
    })

    await waitFor(() => {
      expect(checkAndToastMock).toHaveBeenCalledTimes(3)
      expect(jspdfMock).toHaveBeenCalledTimes(0)
    })
  })

  it('downloads labels sheets', async () => {
    apiMock.mockImplementationOnce(async () => dummyBallots)
    const { getByText } = render(
      <CalculateRiskMeasurement
        audit={statusStates.jurisdictionsInitial}
        isLoading={false}
        setIsLoading={sharedSetIsLoadingMock}
        updateAudit={sharedUpdateAuditMock}
        getStatus={sharedGetStatusMock}
        electionId="1"
      />
    )

    fireEvent.click(getByText('Download Label Sheets for Round 1'), {
      bubbles: true,
    })

    await waitFor(() => {
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
        audit={statusStates.jurisdictionsInitial}
        isLoading={false}
        setIsLoading={sharedSetIsLoadingMock}
        updateAudit={sharedUpdateAuditMock}
        getStatus={sharedGetStatusMock}
        electionId="1"
      />
    )

    fireEvent.click(getByText('Download Placeholders for Round 1'), {
      bubbles: true,
    })

    await waitFor(() => {
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
        audit={statusStates.ballotManifestProcessed}
        isLoading={false}
        setIsLoading={sharedSetIsLoadingMock}
        updateAudit={sharedUpdateAuditMock}
        getStatus={sharedGetStatusMock}
        electionId="1"
      />
    )

    fireEvent.click(
      getByText('Download Aggregated Ballot Retrieval List for Round 1'),
      { bubbles: true }
    )

    expect(window.open).toBeCalledTimes(1)
    expect(window.open).toBeCalledWith(
      `/api/election/1/jurisdiction/jurisdiction-1/1/retrieval-list`
    )
  })

  it('downloads audit report', () => {
    window.open = jest.fn()
    const { getByText } = render(
      <CalculateRiskMeasurement
        audit={statusStates.completeInFirstRound}
        isLoading={false}
        setIsLoading={sharedSetIsLoadingMock}
        updateAudit={sharedUpdateAuditMock}
        getStatus={sharedGetStatusMock}
        electionId="1"
      />
    )

    fireEvent.click(getByText('Download Audit Report'), { bubbles: true })

    expect(window.open).toBeCalledTimes(1)
    expect(window.open).toBeCalledWith(`/api/election/1/report`)
  })

  it('handles errors from api', async () => {
    apiMock.mockReset()
    apiMock.mockRejectedValueOnce({
      message: 'error',
      ok: false,
    })
    const toastSpy = jest.spyOn(toast, 'error').mockImplementation()
    const { getByLabelText, getByText } = render(
      <CalculateRiskMeasurement
        audit={statusStates.ballotManifestProcessed}
        isLoading={false}
        setIsLoading={sharedSetIsLoadingMock}
        updateAudit={sharedUpdateAuditMock}
        getStatus={sharedGetStatusMock}
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

      await waitFor(() => {
        expect(apiMock).toBeCalledTimes(1)
        expect(sharedSetIsLoadingMock).toBeCalledTimes(1)
        expect(sharedUpdateAuditMock).toBeCalledTimes(0)
        expect(toastSpy).toBeCalledTimes(1)
      })
    }
  })

  it('downloads data entry flow sheets', async () => {
    statusStates.firstRoundSampleSizeOptions.online = true
    apiMock.mockImplementationOnce(async () => dummyBallots)
    const { getByText } = render(
      <CalculateRiskMeasurement
        audit={statusStates.firstRoundSampleSizeOptions}
        isLoading={false}
        setIsLoading={sharedSetIsLoadingMock}
        updateAudit={sharedUpdateAuditMock}
        getStatus={sharedGetStatusMock}
        electionId="1"
      />
    )

    fireEvent.click(
      getByText('Download Audit Boards Credentials for Data Entry'),
      {
        bubbles: true,
      }
    )

    await waitFor(() => {
      expect(apiMock).toHaveBeenCalledTimes(1)
      expect(jspdfMock).toHaveBeenCalledTimes(1)
    })
    expect(jspdfInstance.addPage).toHaveBeenCalledTimes(2)
    expect(jspdfInstance.setFontSize).toHaveBeenCalledTimes(6) // 2X per page
    expect(jspdfInstance.setFontStyle).toHaveBeenCalledTimes(6) // 2X per page
    expect(jspdfInstance.splitTextToSize).toHaveBeenCalledTimes(3) // 1X per page
    expect(jspdfInstance.text).toHaveBeenCalledTimes(12) // 4X per page
    expect(jspdfInstance.addImage).toHaveBeenCalledTimes(3) // 1X per page
    expect(jspdfInstance.save).toHaveBeenCalledTimes(1)
  })

  it('renders online mode progress bar', async () => {
    statusStates.ballotManifestProcessed.online = true
    apiMock.mockImplementationOnce(async () => incompleteDummyBallots)
    const { container } = render(
      <CalculateRiskMeasurement
        audit={statusStates.ballotManifestProcessed}
        isLoading
        setIsLoading={sharedSetIsLoadingMock}
        updateAudit={sharedUpdateAuditMock}
        getStatus={sharedGetStatusMock}
        electionId="1"
      />
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    expect(container).toMatchSnapshot()
  })

  it('renders online mode progress bar in multiple rounds', async () => {
    statusStates.multiAuditBoardsAndRounds.online = true
    apiMock.mockImplementationOnce(async () => incompleteDummyBallots)
    const { container } = render(
      <CalculateRiskMeasurement
        audit={statusStates.multiAuditBoardsAndRounds}
        isLoading
        setIsLoading={sharedSetIsLoadingMock}
        updateAudit={sharedUpdateAuditMock}
        getStatus={sharedGetStatusMock}
        electionId="1"
      />
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    expect(container).toMatchSnapshot()
  })
})
