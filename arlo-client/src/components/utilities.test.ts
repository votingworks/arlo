import { api, testNumber } from './utilities'

const response = () =>
  new Response(new Blob([JSON.stringify({ success: true })]))
const badResponse = () =>
  new Response(undefined, {
    status: 404,
    statusText: 'A test error',
  })

const fetchSpy = jest.spyOn(window, 'fetch').mockImplementation()

afterEach(() => {
  fetchSpy.mockClear()
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
      await expect(api('/test', { method: 'GET' })).rejects.toThrow(
        'A test error'
      )
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
})
