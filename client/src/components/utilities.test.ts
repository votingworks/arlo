import { waitFor } from '@testing-library/react'
import { toast } from 'react-toastify'
import { api, testNumber, downloadFile } from './utilities'

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
const badResponseNoMessage = () =>
  new Response(new Blob([JSON.stringify({})]), {
    status: 404,
    statusText: 'A test error',
  })
const badResponseBadParse = () =>
  new Response(new Blob(['{']), {
    status: 404,
    statusText: 'A test error',
  })

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
      expect(window.fetch).toBeCalledWith('/api/test', {
        method: 'GET',
      })
    })

    it('throws an error', async () => {
      fetchSpy.mockImplementationOnce(async () => badResponse())
      const result = await api('/test', { method: 'GET' })

      await expect(toastSpy).toBeCalledWith('An error message')
      await expect(result).toBe(null)
      expect(window.fetch).toBeCalledTimes(1)

      expect(window.fetch).toBeCalledWith('/api/test', {
        method: 'GET',
      })
    })

    it('handles an error without a message', async () => {
      fetchSpy.mockImplementationOnce(async () => badResponseNoMessage())
      const result = await api('/test', { method: 'GET' })

      await expect(toastSpy).toBeCalledWith('A test error')
      await expect(result).toBe(null)
      expect(window.fetch).toBeCalledTimes(1)

      expect(window.fetch).toBeCalledWith('/api/test', {
        method: 'GET',
      })
    })

    it('handles an error that fails parsing', async () => {
      fetchSpy.mockImplementationOnce(async () => badResponseBadParse())
      const result = await api('/test', { method: 'GET' })

      await expect(toastSpy).toBeCalledWith('A test error')
      await expect(result).toBe(null)
      expect(window.fetch).toBeCalledTimes(1)

      expect(window.fetch).toBeCalledWith('/api/test', {
        method: 'GET',
      })
    })

    it('toasts a user-friendly message on 500 errors', async () => {
      fetchSpy.mockImplementationOnce(
        async () =>
          new Response(
            new Blob([
              JSON.stringify({
                errors: [
                  {
                    errorType: 'Internal Server Error',
                    message: 'internal error',
                  },
                ],
              }),
            ]),
            {
              status: 500,
              statusText: 'Internal Server Error',
            }
          )
      )
      const result = await api('/test', { method: 'GET' })

      await expect(toastSpy).toBeCalledWith(
        'Something went wrong. Please try again or contact support.'
      )
      await expect(result).toBe(null)
      expect(window.fetch).toBeCalledTimes(1)
      expect(window.fetch).toBeCalledWith('/api/test', {
        method: 'GET',
      })
    })
  })

  describe('testNumber', () => {
    it('uses default message', () => {
      expect(testNumber(50)(100)).resolves.toBe('Must be smaller than 50')
    })
  })

  describe('downloadFile', () => {
    it('creates a hidden anchor element, attaches the file for download, and clicks it', () => {
      const mockAnchor = {
        href: undefined,
        download: undefined,
        click: jest.fn(),
      }
      document.createElement = jest.fn().mockReturnValue(mockAnchor)
      document.body.appendChild = jest.fn()
      document.body.removeChild = jest.fn()
      URL.createObjectURL = jest.fn().mockReturnValue('test object url')

      const fileContents = new Blob(['test file contents'])
      downloadFile(fileContents, 'test filename.txt')

      expect(document.createElement).toHaveBeenCalledWith('a')
      expect(URL.createObjectURL).toHaveBeenCalledWith(fileContents)
      expect(mockAnchor.href).toEqual('test object url')
      expect(mockAnchor.download).toEqual('test filename.txt')
      expect(mockAnchor.click).toHaveBeenCalled()
      expect(document.body.appendChild).toHaveBeenCalledWith(mockAnchor)
      expect(document.body.removeChild).toHaveBeenCalledWith(mockAnchor)
    })
  })
})
