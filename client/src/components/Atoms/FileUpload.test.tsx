import React from 'react'
import { render as testingLibraryRender, screen } from '@testing-library/react'
import { QueryClientProvider } from 'react-query'
import userEvent from '@testing-library/user-event'
import { ToastContainer } from 'react-toastify'
import {
  useUploadedFile,
  useUploadFiles,
  useDeleteFile,
  IFileUpload,
} from '../useFileUpload'
import FileUpload, { IFileUploadProps } from './FileUpload'
import {
  withMockFetch,
  serverError,
  findAndCloseToast,
  createQueryClient,
} from '../testUtilities'
import { fileInfoMocks } from '../_mocks'

jest.mock('axios')

// Set up a test component that hooks up useFileUpload to FileUpload in the way
// they are used together. We test them together because they are designed to be
// used in concert, so testing their integration is more useful than testing
// them in isolation.
const TestFileUpload = ({
  onFileChange,
  ...props
}: Partial<IFileUploadProps> & { onFileChange?: () => void }) => {
  const uploadedFile = useUploadedFile(['test-key'], '/test', {
    onFileChange: onFileChange || jest.fn(),
  })
  const uploadFiles = useUploadFiles(['test-key'], '/test')
  const deleteFile = useDeleteFile(['test-key'], '/test')
  const fileUpload: IFileUpload = {
    uploadedFile,
    uploadFiles: files => {
      return uploadFiles.mutateAsync({ file: files[0] })
    },
    uploadProgress: uploadFiles.progress,
    deleteFile: () => deleteFile.mutateAsync(),
    downloadFileUrl: '/test/download',
  }
  return (
    <FileUpload
      title="Test File"
      {...fileUpload}
      acceptFileTypes={['csv']}
      {...props}
    />
  )
}

const render = (element: React.ReactElement) =>
  testingLibraryRender(
    <QueryClientProvider client={createQueryClient()}>
      {element}
    </QueryClientProvider>
  )

const testFile = new File(['test content'], 'test-file.csv', {
  type: 'text/csv',
})
const uploadFormData = new FormData()
uploadFormData.append('key', 'path/to/file/file.csv')
uploadFormData.append('otherField', 'canBePassedThrough')
uploadFormData.append('Content-Type', testFile.type)
uploadFormData.append('file', testFile, testFile.name)

const uploadCompleteFormData = new FormData()
uploadCompleteFormData.append('fileName', testFile.name)
uploadCompleteFormData.append('fileType', testFile.type)
uploadCompleteFormData.append('storagePathKey', 'path/to/file/file.csv')

const getUploadUrlMock = {
  url: '/test/file-upload',
  fields: {
    key: 'path/to/file/file.csv',
    otherField: 'canBePassedThrough',
  },
}

describe('FileUpload + useFileUpload', () => {
  it('when no file is uploaded, shows a form to upload a file', async () => {
    const expectedCalls = [
      { url: '/test', response: fileInfoMocks.empty },
      {
        url: '/test/upload-url',
        options: {
          method: 'GET',
          params: { fileType: testFile.type },
        },
        response: getUploadUrlMock,
      },
      {
        url: '/test/file-upload',
        options: { method: 'POST', body: uploadFormData },
        response: { status: 'ok' },
      },
      {
        url: '/test/upload-complete',
        options: { method: 'POST', body: uploadCompleteFormData },
        response: { status: 'ok' },
      },
      { url: '/test', response: fileInfoMocks.processing },
      { url: '/test', response: fileInfoMocks.processed },
    ]
    await withMockFetch(expectedCalls, async () => {
      const onFileChange = jest.fn()
      render(<TestFileUpload onFileChange={onFileChange} />)

      await screen.findByText('Test File')
      expect(onFileChange).not.toHaveBeenCalled()
      const uploadButton = screen.getByRole('button', { name: /Upload/ })
      expect(uploadButton).toBeDisabled()

      const fileInput = screen.getByLabelText('Select a file...')
      userEvent.upload(fileInput, testFile)
      await screen.findByText('test-file.csv')

      userEvent.click(uploadButton)

      await screen.findByText('Uploading')
      expect(uploadButton).toBeDisabled()

      await screen.findByText('Processing')
      expect(uploadButton).toBeDisabled()

      await screen.findByText('Uploaded')
      const fileLink = screen.getByRole('button', { name: /Download/ })
      expect(fileLink).toHaveAttribute('href', '/test/download')
      screen.getByRole('button', { name: /Delete/ })
      expect(onFileChange).toHaveBeenCalledTimes(1)
    })
  })

  it('when a file is uploaded, shows a Delete button', async () => {
    const expectedCalls = [
      { url: '/test', response: fileInfoMocks.processed },
      {
        url: '/test',
        options: { method: 'DELETE' },
        response: { status: 'ok' },
      },
      { url: '/test', response: fileInfoMocks.empty },
    ]
    await withMockFetch(expectedCalls, async () => {
      const onFileChange = jest.fn()
      render(<TestFileUpload onFileChange={onFileChange} />)

      await screen.findByText('Uploaded')
      expect(onFileChange).not.toHaveBeenCalled()
      const deleteButton = screen.getByRole('button', { name: /Delete/ })
      userEvent.click(deleteButton)
      expect(deleteButton).toBeDisabled()
      expect(await screen.findByLabelText('Select a file...')).toHaveValue('')
      expect(onFileChange).toHaveBeenCalledTimes(1)
    })
  })

  it('when a file uploaded fails, shows an error message', async () => {
    const expectedCalls = [
      { url: '/test', response: fileInfoMocks.empty },
      {
        url: '/test/upload-url',
        options: {
          method: 'GET',
          params: { fileType: testFile.type },
        },
        response: getUploadUrlMock,
      },
      {
        url: '/test/file-upload',
        options: { method: 'POST', body: uploadFormData },
        response: { status: 'ok' },
      },
      {
        url: '/test/upload-complete',
        options: { method: 'POST', body: uploadCompleteFormData },
        response: { status: 'ok' },
      },
      { url: '/test', response: fileInfoMocks.errored },
    ]
    await withMockFetch(expectedCalls, async () => {
      render(<TestFileUpload />)

      await screen.findByText('Test File')
      const uploadButton = screen.getByRole('button', { name: /Upload/ })
      expect(uploadButton).toBeDisabled()

      const fileInput = screen.getByLabelText('Select a file...')
      userEvent.upload(fileInput, testFile)
      await screen.findByText('test-file.csv')

      userEvent.click(uploadButton)

      await screen.findByText('Upload Failed')
      screen.getByText('something went wrong')
      const fileLink = screen.getByRole('button', { name: /Download/ })
      expect(fileLink).toHaveAttribute('href', '/test/download')
      screen.getByRole('button', { name: /Delete/ })
    })
  })

  it('supports uploading multiple files', async () => {
    const testFile2 = new File(['test content'], 'test-file-2.csv', {
      type: 'text/csv',
    })
    const formData2 = new FormData()
    formData2.append('files', testFile, testFile.name)
    formData2.append('files', testFile2, testFile2.name)
    const expectedCalls = [
      { url: '/test', response: fileInfoMocks.empty },
      {
        url: '/test/upload-url',
        options: {
          method: 'GET',
          params: { fileType: testFile.type },
        },
        response: getUploadUrlMock,
      },
      {
        url: '/test/file-upload',
        options: { method: 'POST', body: uploadFormData },
        response: { status: 'ok' },
      },
      {
        url: '/test/upload-complete',
        options: { method: 'POST', body: uploadCompleteFormData },
        response: { status: 'ok' },
      },
      { url: '/test', response: fileInfoMocks.processed },
    ]
    await withMockFetch(expectedCalls, async () => {
      render(<TestFileUpload allowMultipleFiles />)

      await screen.findByText('Test File')
      const uploadButton = screen.getByRole('button', { name: /Upload/ })
      expect(uploadButton).toBeDisabled()

      const fileInput = screen.getByLabelText('Select files...')
      userEvent.upload(fileInput, [testFile, testFile2])
      await screen.findByText('2 files selected')

      userEvent.click(uploadButton)
      await screen.findByText('Uploaded')
    })
  })

  it('can have upload disabled when no file uploaded', async () => {
    const expectedCalls = [{ url: '/test', response: fileInfoMocks.empty }]
    await withMockFetch(expectedCalls, async () => {
      render(<TestFileUpload uploadDisabled />)

      await screen.findByText('Test File')
      expect(screen.getByLabelText('Select a file...')).toBeDisabled()
      expect(screen.getByRole('button', { name: /Upload/ })).toBeDisabled()
    })
  })

  it('can have delete disabled when file is uploaded', async () => {
    const expectedCalls = [{ url: '/test', response: fileInfoMocks.processed }]
    await withMockFetch(expectedCalls, async () => {
      render(<TestFileUpload deleteDisabled />)

      await screen.findByText('Uploaded')
      expect(screen.getByRole('button', { name: /Delete/ })).toBeDisabled()
      expect(screen.getByRole('button', { name: /Download/ })).toBeEnabled()
    })
  })

  it('handles an API error on get', async () => {
    const expectedCalls = [serverError('getFile', { url: '/test' })]
    await withMockFetch(expectedCalls, async () => {
      render(
        <>
          <TestFileUpload />
          <ToastContainer />
        </>
      )
      await findAndCloseToast('getFile')
    })
  })

  it('handles an API error on get', async () => {
    const expectedCalls = [
      { url: '/test', response: fileInfoMocks.empty },
      serverError('getFile', {
        url: '/test/upload-url',
        options: {
          method: 'GET',
          params: { fileType: testFile.type },
        } as RequestInit,
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      render(
        <>
          <TestFileUpload />
          <ToastContainer />
        </>
      )
      await screen.findByText('Test File')
      userEvent.upload(screen.getByLabelText('Select a file...'), testFile)
      await screen.findByText('test-file.csv')
      userEvent.click(screen.getByRole('button', { name: /Upload/ }))
      await findAndCloseToast('getFile')
    })
  })

  it('handles an API error on file upload', async () => {
    const expectedCalls = [
      { url: '/test', response: fileInfoMocks.empty },
      {
        url: '/test/upload-url',
        options: {
          method: 'GET',
          params: { fileType: testFile.type },
        },
        response: getUploadUrlMock,
      },
      serverError('postFileUpload', {
        url: '/test/file-upload',
        options: {
          method: 'POST',
          body: uploadFormData,
        },
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      render(
        <>
          <TestFileUpload />
          <ToastContainer />
        </>
      )
      await screen.findByText('Test File')
      userEvent.upload(screen.getByLabelText('Select a file...'), testFile)
      await screen.findByText('test-file.csv')
      userEvent.click(screen.getByRole('button', { name: /Upload/ }))
      await findAndCloseToast('postFileUpload')
    })
  })

  it('handles an API error on file upload completion', async () => {
    const expectedCalls = [
      { url: '/test', response: fileInfoMocks.empty },
      {
        url: '/test/upload-url',
        options: {
          method: 'GET',
          params: { fileType: testFile.type },
        },
        response: getUploadUrlMock,
      },
      {
        url: '/test/file-upload',
        options: { method: 'POST', body: uploadFormData },
        response: { status: 'ok' },
      },
      serverError('postFileComplete', {
        url: '/test/upload-complete',
        options: {
          method: 'POST',
          body: uploadCompleteFormData,
        },
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      render(
        <>
          <TestFileUpload />
          <ToastContainer />
        </>
      )
      await screen.findByText('Test File')
      userEvent.upload(screen.getByLabelText('Select a file...'), testFile)
      await screen.findByText('test-file.csv')
      userEvent.click(screen.getByRole('button', { name: /Upload/ }))
      await findAndCloseToast('postFileComplete')
    })
  })

  it('handles an API error on delete', async () => {
    const expectedCalls = [
      { url: '/test', response: fileInfoMocks.processed },
      serverError('deleteFile', {
        url: '/test',
        options: { method: 'DELETE' },
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      render(
        <>
          <TestFileUpload />
          <ToastContainer />
        </>
      )
      await screen.findByText('Uploaded')
      userEvent.click(screen.getByRole('button', { name: /Delete/ }))
      await findAndCloseToast('deleteFile')
    })
  })
})
