import React from 'react'
import { H5, FileInput, Button, Callout, AnchorButton } from '@blueprintjs/core'
import { useForm } from 'react-hook-form'
import styled from 'styled-components'
import StatusTag from './StatusTag'
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

export interface IFileUploadProps extends IFileUpload {
  title: string
  acceptFileTypes: ('csv' | 'zip' | 'xml')[]
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
        <StatusTag intent="warning" progress={uploadProgress}>
          Uploading
        </StatusTag>
      )
    }

    assert(processing !== null)

    if (!processing.completedAt) {
      return (
        <StatusTag
          intent="primary"
          progress={
            processing.workTotal
              ? processing.workProgress! / processing.workTotal
              : undefined
          }
        >
          Processing
        </StatusTag>
      )
    }

    if (processing.error) {
      return <StatusTag intent="danger">Upload Failed</StatusTag>
    }

    return <StatusTag intent="success">Uploaded</StatusTag>
  })()

  return (
    <form onSubmit={handleSubmit(onUpload)}>
      {/* Set a height so that the height doesn't change based on the status tag
      being present or not */}
      <Row style={{ height: '20px' }}>
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
              (processing !== null && !processing.completedAt)
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
