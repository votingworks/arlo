import { wait } from '@testing-library/react'
import { api, testNumber, poll } from './utilities'

const response = () =>
  new Response(new Blob([JSON.stringify({ success: true })]))
const badResponse = () =>
  new Response(null, {
    status: 404,
    statusText: 'A test error',
  })

const fetchSpy = jest.spyOn(window, 'fetch').mockImplementation()

afterEach(() => {
  fetchSpy.mockClear()
})

describe('utilities.ts', () => {
  describe('api', () => {
    it('calls fetch with electionId', async () => {
      fetchSpy.mockImplementationOnce(async () => response())
      const result = await api('/test', { method: 'GET', electionId: '1' })

      expect(result).toEqual({ success: true })
      expect(window.fetch).toBeCalledTimes(1)
      expect(window.fetch).toBeCalledWith('/election/1/test', {
        method: 'GET',
      })
    })

    it('calls fetch without electionId', async () => {
      fetchSpy.mockImplementationOnce(async () => response())
      const result = await api('/test', { method: 'GET', electionId: '' })

      expect(result).toEqual({ success: true })
      expect(window.fetch).toBeCalledTimes(1)
      expect(window.fetch).toBeCalledWith('/test', {
        method: 'GET',
      })
    })

    it('throws an error', async () => {
      fetchSpy.mockImplementationOnce(async () => badResponse())
      await expect(
        api('/test', { method: 'GET', electionId: '1' })
      ).rejects.toThrow('A test error')
      expect(window.fetch).toBeCalledTimes(1)

      expect(window.fetch).toBeCalledWith('/election/1/test', {
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
        var index = 0
        while (true) yield index++
      })()
      let result = ''
      const condition = async () => j.next().value > 2
      const callback = async () => (result = 'over five')
      const error = async () => (result = 'an error')
      await poll(condition, callback, error)
      await wait(() => {
        expect(result).toBe('over five')
      })
    })

    it('times out', async () => {
      const j = (function* idMaker() {
        var index = 1
        while (true) yield index++
      })()
      let result = ''
      const condition = async () => j.next().value < 1
      const callback = async () => (result = 'over five')
      const error = async () => (result = 'an error')
      await poll(condition, callback, error, 50, 10)
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
      const j = (function* idMaker() {
        var index = 1
        while (true) yield index++
      })()
      let result = ''
      const condition = async () => j.next().value < 1
      const callback = async () => (result = 'over five')
      const error = async () => (result = 'an error')
      await poll(condition, callback, error)
      await wait(() => {
        expect(result).toBe('an error')
        expect(dateSpy).toBeCalledTimes(2)
      })
      dateSpy.mockRestore()
    })
  })
})
