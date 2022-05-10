import React, { useState } from 'react'
import { FileInput, Button, Colors, ProgressBar } from '@blueprintjs/core'
import { useForm } from 'react-hook-form'
import styled from 'styled-components'
import StatusTag from './StatusTag'
import { IFileUpload } from '../useFileUpload'

const ErrorP = styled.p`
  margin-top: 10px;
  color: ${Colors.RED3};
`

interface IFileUploadProps extends IFileUpload {
  uploadFiles: (files: FileList) => Promise<void>
  acceptFileType: 'csv' | 'zip'
  allowMultipleFiles?: boolean
  disabled?: boolean
}

const FileUpload = ({
  uploadedFile,
  uploadFiles,
  deleteFile,
  downloadFileUrl,
  acceptFileType,
  allowMultipleFiles = false,
  disabled = false,
}: IFileUploadProps) => {
  const { register, handleSubmit, formState, watch } = useForm<{
    files: FileList
  }>({ mode: 'onTouched' })
  const [isReplacing, setIsReplacing] = useState(false)

  if (uploadedFile.isLoading) {
    return null
  }
  if (!uploadedFile.isSuccess) {
    return <ErrorP>Error loading file info</ErrorP>
  }

  const { file, processing, upload } = uploadedFile.data

  if (!upload && (!file || isReplacing)) {
    const onUpload = async ({ files }: { files: FileList }) => {
      await uploadFiles(files)
      setIsReplacing(false)
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
              accept: `.${acceptFileType}`,
              name: 'files',
              multiple: allowMultipleFiles,
              ref: register({ required: true }),
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
            disabled={disabled || !formState.isValid}
          >
            Upload File
          </Button>
        </p>
      </form>
    )
  }

  if (upload) {
    const fileName =
      upload.files.length === 1
        ? upload.files[0].name
        : `${upload.files.length} files`
    return (
      <form>
        <p>
          <StatusTag intent="warning">Uploading</StatusTag>
          <span style={{ marginLeft: '15px' }}>{fileName}</span>
        </p>
        <ProgressBar
          key="uploading"
          stripes={false}
          intent="warning"
          value={upload.progress}
        />
      </form>
    )
  }

  if (!(file && processing)) {
    throw new Error('Invalid state')
  }

  if (!processing.completedAt) {
    return (
      <form>
        <p>
          <StatusTag intent="primary">Processing</StatusTag>
          <span style={{ marginLeft: '15px' }}>{file.name}</span>
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
    <form onSubmit={handleSubmit(deleteFile)}>
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
        <Button disabled={disabled} onClick={() => setIsReplacing(true)}>
          Replace File
        </Button>
        <Button
          type="submit"
          loading={formState.isSubmitting}
          disabled={disabled}
          style={{ marginLeft: '5px' }}
        >
          Delete File
        </Button>
      </p>
    </form>
  )
}

export default FileUpload
