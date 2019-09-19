import api from './utilities'

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
