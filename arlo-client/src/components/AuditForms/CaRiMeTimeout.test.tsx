import React from 'react'
import { render, fireEvent, wait } from '@testing-library/react'
import { toast } from 'react-toastify'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'
import { statusStates } from './_mocks'
import * as utilities from '../utilities'
import { RoundContest } from '../../types'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()

const setIsLoadingMock = jest.fn()
const updateAuditMock = jest.fn()
const getStatusMock = jest.fn().mockImplementation(async () => statusStates[6])
const toastSpy = jest.spyOn(toast, 'error').mockImplementation()

beforeEach(() => {
  setIsLoadingMock.mockClear()
  updateAuditMock.mockClear()
  getStatusMock.mockClear()
  toastSpy.mockClear()
  apiMock.mockClear()
})

describe('CalculateRiskMeasurement poll timeout', () => {
  it.skip('using only the relevant function', async () => {
    const dateIncrementor = (function*() {
      let i = 10
      while (true) {
        i += 130000
        yield i
      }
    })()

    const realDate = global.Date.now
    global.Date.now = jest
      .fn()
      .mockImplementation(() => dateIncrementor.next().value)

    const condition = async () => {
      const { rounds } = await getStatusMock()
      const { contests } = rounds[rounds.length - 1]
      return (
        !!contests.length && contests.every((c: RoundContest) => !!c.sampleSize)
      )
    }

    const complete = () => {
      updateAuditMock()
      setIsLoadingMock(false)
    }

    await utilities.poll(condition, complete, (err: Error) =>
      toast.error(err.message)
    )

    await wait(() => {
      expect(global.Date.now).toBeCalledTimes(2)
      expect(setIsLoadingMock).toBeCalledTimes(0)
      expect(getStatusMock).toBeCalledTimes(1)
      expect(updateAuditMock).toBeCalledTimes(0)
      expect(toastSpy).toBeCalledTimes(1)
    })

    global.Date.now = realDate
  })

  it.skip(`using the whole component`, async () => {
    const dateIncrementor = (function*() {
      let i = 10
      while (true) {
        i += 130000
        yield i
      }
    })()
    const realDate = global.Date.now
    global.Date.now = jest
      .fn()
      .mockImplementation(() => dateIncrementor.next().value)

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
      expect(apiMock).toBeCalled()
      expect(setIsLoadingMock).toBeCalledTimes(1)
      expect(getStatusMock).toBeCalled()
      expect(updateAuditMock).toBeCalledTimes(0)
      expect(toastSpy).toBeCalledTimes(1)
    })

    global.Date.now = realDate
  })
})
