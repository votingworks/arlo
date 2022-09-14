import React from 'react'
import { FileInput, Button, Colors, ProgressBar } from '@blueprintjs/core'
import { useForm } from 'react-hook-form'
import styled from 'styled-components'
import StatusTag from './StatusTag'
import { IFileUpload } from '../useFileUpload'
import AsyncButton from './AsyncButton'

const ErrorP = styled.p`
  margin-top: 10px;
  color: ${Colors.RED3};
`

export interface IFileUploadProps extends IFileUpload {
  acceptFileTypes: ('csv' | 'zip')[]
  allowMultipleFiles?: boolean
  disabled?: boolean
}

const FileUpload: React.FC<IFileUploadProps> = ({
  uploadedFile,
  uploadFiles,
  uploadProgress,
  deleteFile,
  downloadFileUrl,
  acceptFileTypes,
  allowMultipleFiles = false,
  disabled = false,
}) => {
  const { register, handleSubmit, formState, watch } = useForm<{
    files: FileList
  }>({ mode: 'onTouched' })

  if (!uploadedFile.isSuccess) return null

  const { file, processing } = uploadedFile.data

  if (!uploadProgress && !file) {
    const onUpload = async ({ files }: { files: FileList }) => {
      try {
        await uploadFiles(Array.from(files))
      } catch (error) {
        // Do nothing - toasting handled by queryClient
      }
    }

    const files = watch('files')
    const numFiles = files ? files.length : 0

    return (
      <form onSubmit={handleSubmit(onUpload)}>
        <p>
          <StatusTag>No file uploaded</StatusTag>
        </p>
        <p>
          <FileInput
            inputProps={{
              accept: acceptFileTypes.map(fileType => `.${fileType}`).join(','),
              name: 'files',
              multiple: allowMultipleFiles,
              ref: register(),
            }}
            hasSelection={numFiles > 0}
            text={(() => {
              if (numFiles === 0)
                return allowMultipleFiles
                  ? 'Select files...'
                  : 'Select a file...'
              if (numFiles === 1) return files[0].name
              return `${numFiles} files selected`
            })()}
            disabled={disabled || formState.isSubmitting}
          />
        </p>
        <p>
          <Button
            type="submit"
            intent="primary"
            loading={formState.isSubmitting}
            disabled={disabled || numFiles === 0}
          >
            {allowMultipleFiles ? 'Upload Files' : 'Upload File'}
          </Button>
        </p>
      </form>
    )
  }

  if (uploadProgress) {
    return (
      <form>
        <p>
          <StatusTag intent="warning">Uploading</StatusTag>
        </p>
        <ProgressBar
          key="uploading"
          stripes={false}
          intent="warning"
          value={uploadProgress}
        />
      </form>
    )
  }

  /* istanbul ignore next */
  if (!(file && processing)) {
    throw new Error('Invalid state')
  }

  if (!processing.completedAt) {
    return (
      <form>
        <p>
          <StatusTag intent="primary">Processing</StatusTag>
        </p>
        {processing.workTotal && (
          <ProgressBar
            key="processing"
            stripes={false}
            intent="primary"
            value={processing.workProgress! / processing.workTotal}
          />
        )}
      </form>
    )
  }

  const { error } = processing
  return (
    <form>
      <p>
        {error ? (
          <StatusTag intent="danger">Upload failed</StatusTag>
        ) : (
          <StatusTag intent="success">Uploaded</StatusTag>
        )}
        <a
          href={downloadFileUrl}
          target="_blank"
          rel="noopener noreferrer"
          style={{ marginLeft: '15px' }}
        >
          {file.name}
        </a>
      </p>
      {error && <ErrorP>{error}</ErrorP>}
      <p>
        <AsyncButton disabled={disabled} onClick={deleteFile}>
          Delete File
        </AsyncButton>
      </p>
    </form>
  )
}

export default FileUpload
