import React from 'react'
import { H5, FileInput, Button, Callout, AnchorButton } from '@blueprintjs/core'
import { useForm } from 'react-hook-form'
import styled from 'styled-components'
import StatusTag, { StatusTagWithProgress } from './StatusTag'
import { IFileUpload } from '../useFileUpload'
import AsyncButton from './AsyncButton'
import { assert } from '../utilities'

const Row = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  &:not(:last-child) {
    margin-bottom: 10px;
  }
`

const buttonAndTagWidth = '115px' // Wide enough for the longest text

const FileStatusTag = styled(StatusTag)`
  width: ${buttonAndTagWidth};
  text-align: center;
`

const FileStatusTagWithProgress = styled(StatusTagWithProgress)`
  width: ${buttonAndTagWidth};
  text-align: center;
`

export interface IFileUploadProps extends IFileUpload {
  title: string
  acceptFileTypes: ('csv' | 'zip')[]
  allowMultipleFiles?: boolean
  uploadDisabled?: boolean
  deleteDisabled?: boolean
  additionalFields?: React.ReactNode
}

const FileUpload: React.FC<IFileUploadProps> = ({
  title,
  uploadedFile,
  uploadFiles,
  uploadProgress,
  deleteFile,
  downloadFileUrl,
  acceptFileTypes,
  allowMultipleFiles = false,
  uploadDisabled = false,
  deleteDisabled = false,
  additionalFields,
}: IFileUploadProps) => {
  const { register, handleSubmit, formState, watch, reset } = useForm<{
    files: FileList
  }>({ mode: 'onTouched' })

  if (!uploadedFile.isSuccess) return null

  const onUpload = async ({ files }: { files: FileList }) => {
    try {
      await uploadFiles(Array.from(files))
    } catch (error) {
      // Do nothing - toasting handled by queryClient
    }
  }

  const onDelete = async () => {
    try {
      await deleteFile()
      reset()
    } catch (error) {
      // Do nothing - toasting handled by queryClient
    }
  }

  const { file, processing } = uploadedFile.data

  const selectedFiles = watch('files')
  const numSelectedFiles = selectedFiles ? selectedFiles.length : 0

  const statusTag = (() => {
    if (!uploadProgress && !file) return null

    if (uploadProgress !== undefined) {
      return (
        <FileStatusTagWithProgress intent="warning" progress={uploadProgress}>
          Uploading
        </FileStatusTagWithProgress>
      )
    }

    assert(processing !== null)

    if (!processing.completedAt) {
      return processing.workTotal ? (
        <FileStatusTagWithProgress
          intent="primary"
          progress={processing.workProgress! / processing.workTotal}
        >
          Processing
        </FileStatusTagWithProgress>
      ) : (
        <FileStatusTag intent="primary">Processing</FileStatusTag>
      )
    }

    if (processing.error) {
      return <FileStatusTag intent="danger">Upload Failed</FileStatusTag>
    }

    return <FileStatusTag intent="success">Uploaded</FileStatusTag>
  })()

  return (
    <form onSubmit={handleSubmit(onUpload)}>
      <Row>
        <H5 style={{ marginBottom: 0 }}>{title}</H5>
        {statusTag}
      </Row>
      {processing?.error && (
        <Row>
          <Callout intent="danger">
            <div className="bp3-text-small">{processing.error}</div>
          </Callout>
        </Row>
      )}
      {additionalFields && <Row>{additionalFields}</Row>}
      <Row>
        <FileInput
          inputProps={{
            accept: acceptFileTypes.map(fileType => `.${fileType}`).join(','),
            name: 'files',
            multiple: allowMultipleFiles,
            ref: register(),
          }}
          hasSelection={numSelectedFiles > 0}
          text={(() => {
            if (file) return file.name
            if (numSelectedFiles === 0)
              return allowMultipleFiles ? 'Select files...' : 'Select a file...'
            if (numSelectedFiles === 1) return selectedFiles[0].name
            return `${numSelectedFiles} files selected`
          })()}
          disabled={uploadDisabled || formState.isSubmitting || file !== null}
          fill
        />
      </Row>
      <Row style={{ justifyContent: 'flex-end' }}>
        {!processing?.completedAt ? (
          <Button
            type="submit"
            intent="primary"
            icon="upload"
            disabled={
              uploadDisabled ||
              numSelectedFiles === 0 ||
              formState.isSubmitting ||
              (processing && !processing.completedAt)
            }
            style={{ width: buttonAndTagWidth }}
          >
            Upload
          </Button>
        ) : (
          <>
            <AnchorButton
              icon="download"
              href={downloadFileUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{ marginRight: '5px', width: buttonAndTagWidth }}
            >
              Download
            </AnchorButton>
            <AsyncButton
              icon="delete"
              onClick={onDelete}
              disabled={deleteDisabled}
              style={{ width: buttonAndTagWidth }}
            >
              Delete
            </AsyncButton>
          </>
        )}
      </Row>
    </form>
  )
}

export default FileUpload
