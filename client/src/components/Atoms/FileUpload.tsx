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

const FileUploadForm = styled.form``

interface IFileUploadProps extends IFileUpload {
  acceptFileType: 'csv' | 'zip'
  allowMultipleFiles?: boolean
  disabled?: boolean
}

const FileUpload = ({
  uploadedFile,
  uploadFiles,
  deleteFile,
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
      const formData = new FormData()
      const formKey = 'manifest' // TODO - make this configurable
      for (const f of files) formData.append(formKey, f, f.name)
      await uploadFiles.mutateAsync(formData)
      setIsReplacing(false)
    }

    const files = watch('files')
    const numFiles = files ? files.length : 0

    return (
      <FileUploadForm onSubmit={handleSubmit(onUpload)}>
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
      </FileUploadForm>
    )
  }

  if (upload) {
    const fileName =
      upload.files.length === 1
        ? upload.files[0].name
        : `${upload.files.length} files`
    return (
      <FileUploadForm>
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
      </FileUploadForm>
    )
  }

  if (!(file && processing)) {
    throw new Error('Invalid state')
  }

  if (!processing.completedAt) {
    return (
      <FileUploadForm>
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
      </FileUploadForm>
    )
  }

  const { error } = processing
  return (
    <FileUploadForm
      onSubmit={deleteFile && handleSubmit(() => deleteFile.mutateAsync())}
    >
      <p>
        {error ? (
          <StatusTag intent="danger">Upload Failed</StatusTag>
        ) : (
          <StatusTag intent="success">Uploaded</StatusTag>
        )}
        <a href="/" style={{ marginLeft: '15px' }}>
          {file.name}
        </a>
      </p>
      {error && <ErrorP>{error}</ErrorP>}
      <p>
        <Button disabled={disabled} onClick={() => setIsReplacing(true)}>
          Replace File
        </Button>
        {deleteFile && (
          <Button
            type="submit"
            loading={formState.isSubmitting}
            disabled={disabled}
            style={{ marginLeft: '5px' }}
          >
            Delete File
          </Button>
        )}
      </p>
    </FileUploadForm>
  )
}

export default FileUpload
