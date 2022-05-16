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
  mockOfType,
  serverError,
  findAndCloseToast,
} from '../testUtilities'
import { queryClient } from '../../App'
import { IFileInfo, FileProcessingStatus } from '../useCSV'

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
      const formData = new FormData()
      for (const file of files) {
        formData.append('files', file, file.name)
      }
      return uploadFiles.mutateAsync(formData)
    },
    uploadProgress: uploadFiles.progress,
    deleteFile: () => deleteFile.mutateAsync(),
    downloadFileUrl: '/test/download',
  }
  return <FileUpload {...fileUpload} acceptFileType="csv" {...props} />
}

const render = (element: React.ReactElement) =>
  testingLibraryRender(
    <QueryClientProvider client={queryClient}>{element}</QueryClientProvider>
  )

const fileInfoMocks = mockOfType<IFileInfo>()({
  empty: { file: null, processing: null },
  processing: {
    file: {
      name: 'test-file.csv',
      uploadedAt: '2020-06-08T21:39:05.765+00:00',
    },
    processing: {
      status: FileProcessingStatus.PROCESSING,
      startedAt: '2020-06-08T21:39:05.765+00:00',
      completedAt: null,
      error: null,
      workProgress: 1,
      workTotal: 2,
    },
  },
  processed: {
    file: {
      name: 'test-file.csv',
      uploadedAt: '2020-06-08T21:39:05.765+00:00',
    },
    processing: {
      status: FileProcessingStatus.PROCESSED,
      startedAt: '2020-06-08T21:39:05.765+00:00',
      completedAt: '2020-06-08T21:40:05.765+00:00',
      error: null,
    },
  },
  errored: {
    file: {
      name: 'test-file.csv',
      uploadedAt: '2020-06-08T21:39:05.765+00:00',
    },
    processing: {
      status: FileProcessingStatus.ERRORED,
      startedAt: '2020-06-08T21:39:05.765+00:00',
      completedAt: '2020-06-08T21:40:05.765+00:00',
      error: 'something went wrong',
    },
  },
})

const testFile = new File(['test content'], 'test-file.csv', {
  type: 'text/csv',
})
const formData = new FormData()
formData.append('files', testFile, testFile.name)

describe('FileUpload + useFileUpload', () => {
  it('when no file is uploaded, shows a form to upload a file', async () => {
    const expectedCalls = [
      { url: '/test', response: fileInfoMocks.empty },
      {
        url: '/test',
        options: { method: 'PUT', body: formData },
        response: { status: 'ok' },
      },
      { url: '/test', response: fileInfoMocks.processing },
      { url: '/test', response: fileInfoMocks.processed },
    ]
    await withMockFetch(expectedCalls, async () => {
      const onFileChange = jest.fn()
      render(<TestFileUpload onFileChange={onFileChange} />)

      await screen.findByText('No file uploaded')
      expect(onFileChange).not.toHaveBeenCalled()
      const uploadButton = screen.getByRole('button', { name: 'Upload File' })
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
      const fileLink = screen.getByRole('link', { name: 'test-file.csv' })
      expect(fileLink).toHaveAttribute('href', '/test/download')
      screen.getByRole('button', { name: 'Delete File' })
      expect(onFileChange).toHaveBeenCalledTimes(1)
    })
  })

  it('when a file is uploaded, shows a delete file button', async () => {
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
      const deleteButton = screen.getByRole('button', { name: 'Delete File' })
      userEvent.click(deleteButton)
      expect(deleteButton).toBeDisabled()
      await screen.findByText('No file uploaded')
      expect(onFileChange).toHaveBeenCalledTimes(1)
    })
  })

  it('when a file uploaded fails, shows an error message', async () => {
    const expectedCalls = [
      { url: '/test', response: fileInfoMocks.empty },
      {
        url: '/test',
        options: { method: 'PUT', body: formData },
        response: { status: 'ok' },
      },
      { url: '/test', response: fileInfoMocks.errored },
    ]
    await withMockFetch(expectedCalls, async () => {
      render(<TestFileUpload />)

      await screen.findByText('No file uploaded')
      const uploadButton = screen.getByRole('button', { name: 'Upload File' })
      expect(uploadButton).toBeDisabled()

      const fileInput = screen.getByLabelText('Select a file...')
      userEvent.upload(fileInput, testFile)
      await screen.findByText('test-file.csv')

      userEvent.click(uploadButton)

      await screen.findByText('Upload failed')
      screen.getByText('something went wrong')
      const fileLink = screen.getByRole('link', { name: 'test-file.csv' })
      expect(fileLink).toHaveAttribute('href', '/test/download')
      screen.getByRole('button', { name: 'Delete File' })
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
        url: '/test',
        options: { method: 'PUT', body: formData2 },
        response: { status: 'ok' },
      },
      { url: '/test', response: fileInfoMocks.processed },
    ]
    await withMockFetch(expectedCalls, async () => {
      render(<TestFileUpload allowMultipleFiles />)

      await screen.findByText('No file uploaded')
      const uploadButton = screen.getByRole('button', { name: 'Upload Files' })
      expect(uploadButton).toBeDisabled()

      const fileInput = screen.getByLabelText('Select files...')
      userEvent.upload(fileInput, [testFile, testFile2])
      await screen.findByText('2 files selected')

      userEvent.click(uploadButton)
      await screen.findByText('Uploaded')
    })
  })

  it('can be disabled when no file uploaded', async () => {
    const expectedCalls = [{ url: '/test', response: fileInfoMocks.empty }]
    await withMockFetch(expectedCalls, async () => {
      render(<TestFileUpload disabled />)

      await screen.findByText('No file uploaded')
      expect(screen.getByLabelText('Select a file...')).toBeDisabled()
      expect(screen.getByRole('button', { name: 'Upload File' })).toBeDisabled()
    })
  })

  it('can be disabled when file is uploaded', async () => {
    const expectedCalls = [{ url: '/test', response: fileInfoMocks.processed }]
    await withMockFetch(expectedCalls, async () => {
      render(<TestFileUpload disabled />)

      await screen.findByText('Uploaded')
      expect(screen.getByRole('button', { name: 'Delete File' })).toBeDisabled()
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

  it('handles an API error on put', async () => {
    const expectedCalls = [
      { url: '/test', response: fileInfoMocks.empty },
      serverError('putFile', {
        url: '/test',
        options: {
          method: 'PUT',
          body: formData,
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
      await screen.findByText('No file uploaded')
      userEvent.upload(screen.getByLabelText('Select a file...'), testFile)
      await screen.findByText('test-file.csv')
      userEvent.click(screen.getByRole('button', { name: 'Upload File' }))
      await findAndCloseToast('putFile')
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
      userEvent.click(screen.getByRole('button', { name: 'Delete File' }))
      await findAndCloseToast('deleteFile')
    })
  })
})
