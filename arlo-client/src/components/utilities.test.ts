import { wait } from '@testing-library/react'
import { toast } from 'react-toastify'
import { api, testNumber, poll, checkAndToast } from './utilities'

const response = () =>
  new Response(new Blob([JSON.stringify({ success: true })]))
const badResponse = () =>
  new Response(
    new Blob([JSON.stringify({ errors: [{ message: 'An error message' }] })]),
    {
      status: 404,
      statusText: 'A test error',
    }
  )

const fetchSpy = jest.spyOn(window, 'fetch').mockImplementation()
const toastSpy = jest.spyOn(toast, 'error').mockImplementation()

afterEach(() => {
  fetchSpy.mockClear()
  toastSpy.mockClear()
})

describe('utilities.ts', () => {
  describe('api', () => {
    it('calls fetch', async () => {
      fetchSpy.mockImplementationOnce(async () => response())
      const result = await api('/test', { method: 'GET' })

      expect(result).toEqual({ success: true })
      expect(window.fetch).toBeCalledTimes(1)
      expect(window.fetch).toBeCalledWith('/test', {
        method: 'GET',
      })
    })

    it('throws an error', async () => {
      fetchSpy.mockImplementationOnce(async () => badResponse())
      const result = api('/test', { method: 'GET' })

      await expect(result).rejects.toHaveProperty('message', 'An error message')
      await expect(result).rejects.toHaveProperty('response')
      expect(window.fetch).toBeCalledTimes(1)

      expect(window.fetch).toBeCalledWith('/test', {
        method: 'GET',
      })
    })
  })

  describe('testNumber', () => {
    it('uses default message', () => {
      expect(testNumber(50)(100)).resolves.toBe('Must be smaller than 50')
    })
  })

  describe('poll', () => {
    it('iterates', async () => {
      const j = (function* idMaker() {
        let index = 0
        while (true) yield (index += 1)
      })()
      let result = ''
      const condition = async () => j.next().value > 2
      const callback = () => {
        result = 'callback completed'
      }
      const error = () => {
        result = 'an error'
      }
      poll(condition, callback, error)
      await wait(() => {
        expect(result).toBe('callback completed')
      })
    })

    it('times out', async () => {
      let result = ''
      const condition = async () => false
      const callback = () => {
        result = 'callback completed'
      }
      const error = () => {
        result = 'an error'
      }
      poll(condition, callback, error, 50, 10)
      await wait(() => {
        expect(result).toBe('an error')
      })
    })

    it('times out with spies', async () => {
      const startDate: number = Date.now()
      const lateDate: number = startDate + 130000
      const dateSpy = jest
        .spyOn(Date, 'now')
        .mockReturnValueOnce(startDate)
        .mockReturnValueOnce(lateDate)
      let result = ''
      const condition = async () => false
      const callback = () => {
        result = 'callback completed'
      }
      const error = () => {
        result = 'an error'
      }
      poll(condition, callback, error)
      await wait(() => {
        expect(result).toBe('an error')
        expect(dateSpy).toBeCalledTimes(2)
      })
      dateSpy.mockRestore()
    })
  })

  describe('checkAndToast', () => {
    it('toasts errors', () => {
      expect(checkAndToast({ errors: [{ message: 'error' }] })).toBeTruthy()
      expect(toastSpy).toBeCalledTimes(1)
    })

    it('returns false without errors', () => {
      expect(checkAndToast({})).toBeFalsy()
      expect(toastSpy).toBeCalledTimes(0)
    })

    it('handles falsy input and nonobject inputs', () => {
      expect(checkAndToast(null)).toBeFalsy()
      expect(checkAndToast('')).toBeFalsy()
      expect(toastSpy).toBeCalledTimes(0)
    })
  })
})
