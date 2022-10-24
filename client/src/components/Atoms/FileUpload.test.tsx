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
        url: '/test',
        options: { method: 'PUT', body: formData },
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
        url: '/test',
        options: { method: 'PUT', body: formData2 },
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
      await screen.findByText('Test File')
      userEvent.upload(screen.getByLabelText('Select a file...'), testFile)
      await screen.findByText('test-file.csv')
      userEvent.click(screen.getByRole('button', { name: /Upload/ }))
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
      userEvent.click(screen.getByRole('button', { name: /Delete/ }))
      await findAndCloseToast('deleteFile')
    })
  })
})
