import api from './utilities'

const response = new Response(new Blob([JSON.stringify({ success: true })]))
const mockFetchSuccessPromise = Promise.resolve(response)
const badResponse = new Response(null, {
  status: 404,
  statusText: 'A test error',
})
const mockFetchFailurePromise = Promise.resolve(badResponse)
jest
  .spyOn(window, 'fetch')
  .mockImplementationOnce(() => mockFetchSuccessPromise)
  .mockImplementationOnce(() => mockFetchFailurePromise)

const options = { method: 'GET' }

describe('utilities.ts', () => {
  it('calls fetch', async () => {
    const result = await api('/test', options)

    expect(result).toMatchObject({ success: true })
    expect(window.fetch).toHaveBeenCalledTimes(1)
    expect(window.fetch).toHaveBeenCalledWith('/test', options)
  })

  it('throws an error', async () => {
    await expect(api('/test', options)).rejects.toThrow('A test error')
    expect(window.fetch).toHaveBeenCalledTimes(2)

    expect(window.fetch).toHaveBeenCalledWith('/test', options)
  })
})
