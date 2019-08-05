import api from './utilities'

const mockFetchSuccessPromise = Promise.resolve({
  json: () => Promise.resolve({ success: true }),
  ok: true,
})
const mockFetchFailurePromise = Promise.resolve({
  statusText: 'A test error',
  ok: false,
})
;(jest as any)
  .spyOn(global, 'fetch')
  .mockImplementationOnce(() => mockFetchSuccessPromise)
  .mockImplementationOnce(() => mockFetchFailurePromise)

const options = { method: 'GET' }

describe('utilities.ts', () => {
  it('calls fetch', async () => {
    const result = await api('/test', options)

    expect(result).toMatchObject({ success: true })
    expect((global as any).fetch).toHaveBeenCalledTimes(1)
    expect((global as any).fetch).toHaveBeenCalledWith('/test', options)
  })

  it('throws an error', async () => {
    await expect(api('/test', options)).rejects.toThrow('A test error')
    expect((global as any).fetch).toHaveBeenCalledTimes(2)

    expect((global as any).fetch).toHaveBeenCalledWith('/test', options)
  })
})
