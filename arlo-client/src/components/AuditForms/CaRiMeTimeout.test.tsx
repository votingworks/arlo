import React from 'react'
import { render, fireEvent, wait } from '@testing-library/react'
import { toast } from 'react-toastify'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'
import { statusStates } from './_mocks'
import * as utilities from '../utilities'

jest.spyOn(HTMLCanvasElement.prototype, 'getContext').mockImplementation()

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()

jest.mock('jspdf')

const setIsLoadingMock = jest.fn()
const updateAuditMock = jest.fn()
const getStatusMock = jest.fn().mockImplementation(async () => statusStates[5])
const toastSpy = jest.spyOn(toast, 'error').mockImplementation()

beforeEach(() => {
  setIsLoadingMock.mockClear()
  updateAuditMock.mockClear()
  getStatusMock.mockClear()
  toastSpy.mockClear()
  apiMock.mockClear()
})

describe('CalculateRiskMeasurement poll timeout', () => {
  it(`handles background process timeout`, async () => {
    const realDate = global.Date.now
    console.log('calculateriskmeasurement timeout test')
    // const startDate: number = Date.now()
    const startDate = 10
    const lateDate: number = startDate + 130000
    global.Date.now = jest
      .fn()
      .mockReturnValueOnce(startDate)
      .mockReturnValueOnce(lateDate)
    // const dateSpy = jest
    //   .spyOn(Date, 'now')
    //   .mockImplementationOnce(() => startDate)
    //   .mockImplementationOnce(() => lateDate)
    console.log('startDate:', startDate, 'lateDate:', lateDate)
    getStatusMock.mockImplementation(async () => statusStates[6])
    apiMock.mockImplementation(async () => ({
      message: 'success',
      ok: true,
    }))
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
      expect(global.Date.now).toBeCalled()
      expect(global.Date.now).toBeCalledTimes(2)
      expect(apiMock).toBeCalled()
      expect(setIsLoadingMock).toBeCalledTimes(1)
      expect(getStatusMock).toBeCalled()
      expect(updateAuditMock).toBeCalledTimes(0)
      expect(toastSpy).toBeCalledTimes(1)
    })
    // dateSpy.mockRestore()
    global.Date.now = realDate
  })
})
