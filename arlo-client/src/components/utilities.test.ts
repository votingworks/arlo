import api, { testNumber } from './utilities'

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
      expect(window.fetch).toHaveBeenCalledTimes(1)
      expect(window.fetch).toHaveBeenCalledWith('/election/1/test', {
        method: 'GET',
      })
    })

    it('calls fetch without electionId', async () => {
      fetchSpy.mockImplementationOnce(async () => response())
      const result = await api('/test', { method: 'GET', electionId: '' })

      expect(result).toEqual({ success: true })
      expect(window.fetch).toHaveBeenCalledTimes(1)
      expect(window.fetch).toHaveBeenCalledWith('/test', {
        method: 'GET',
      })
    })

    it('throws an error', async () => {
      fetchSpy.mockImplementationOnce(async () => badResponse())
      await expect(
        api('/test', { method: 'GET', electionId: '1' })
      ).rejects.toThrow('A test error')
      expect(window.fetch).toHaveBeenCalledTimes(1)

      expect(window.fetch).toHaveBeenCalledWith('/election/1/test', {
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
