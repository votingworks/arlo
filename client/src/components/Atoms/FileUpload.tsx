import React, { useState } from 'react'
import {
  H5,
  FileInput,
  Button,
  Callout,
  AnchorButton,
  HTMLSelect,
} from '@blueprintjs/core'
import { useForm } from 'react-hook-form'
import styled from 'styled-components'
import StatusTag from './StatusTag'
import { IFileUpload, ICvrsFileUpload } from '../useFileUpload'
import AsyncButton from './AsyncButton'
import { assert } from '../utilities'
import { CvrFileType } from '../useCSV'

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
  title?: string
  acceptFileTypes: ('csv' | 'zip' | 'xml')[]
  allowMultipleFiles?: boolean
  uploadDisabled?: boolean
  deleteDisabled?: boolean
  additionalFields?: React.ReactNode
}

export const FileUpload: React.FC<IFileUploadProps> = ({
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
        <StatusTag intent="warning" large progress={uploadProgress}>
          Uploading
        </StatusTag>
      )
    }

    assert(processing !== null)

    if (!processing.completedAt) {
      return (
        <StatusTag
          intent="primary"
          large
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
      return (
        <StatusTag intent="danger" large>
          Upload Failed
        </StatusTag>
      )
    }

    return (
      <StatusTag intent="success" large>
        Uploaded
      </StatusTag>
    )
  })()

  return (
    <form onSubmit={handleSubmit(onUpload)}>
      {/* Set a height so that the height doesn't change based on the status tag
      being present or not */}
      {/* <Row style={{ height: '20px' }}>
        {title && <H5 style={{ marginBottom: 0 }}>{title}</H5>}
      </Row> */}
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
      <Row style={{ justifyContent: 'space-between' }}>
        {statusTag || <div />}
        <div>
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
        </div>
      </Row>
      {processing?.error && (
        <Row>
          <Callout intent="danger">
            <div className="bp3-text-small">{processing.error}</div>
          </Callout>
        </Row>
      )}
    </form>
  )
}

interface ICvrsFileUploadProps {
  cvrsUpload: ICvrsFileUpload
  uploadDisabled?: boolean
  deleteDisabled?: boolean
}

export const CvrsFileUpload: React.FC<ICvrsFileUploadProps> = ({
  cvrsUpload,
  uploadDisabled,
  deleteDisabled,
}) => {
  assert(cvrsUpload.uploadedFile.isSuccess)
  const [selectedCvrFileType, setSelectedCvrFileType] = useState<
    CvrFileType | undefined
  >(cvrsUpload.uploadedFile.data?.file?.cvrFileType)
  const [isUploading, setIsUploading] = useState(false)

  const uploadFiles = async (files: File[]) => {
    setIsUploading(true)
    try {
      await cvrsUpload.uploadFiles(files, selectedCvrFileType!)
    } finally {
      setIsUploading(false)
    }
  }

  const cvrs = cvrsUpload.uploadedFile.data

  return (
    <>
      <FileUpload
        title="Cast Vote Records (CVR)"
        {...cvrsUpload}
        uploadFiles={uploadFiles}
        acceptFileTypes={
          selectedCvrFileType === CvrFileType.HART ? ['zip', 'csv'] : ['csv']
        }
        allowMultipleFiles={
          selectedCvrFileType === CvrFileType.ESS ||
          selectedCvrFileType === CvrFileType.HART
        }
        uploadDisabled={uploadDisabled || (!cvrs.file && !selectedCvrFileType)}
        deleteDisabled={deleteDisabled}
        additionalFields={
          <div>
            <label htmlFor="cvrFileType">Voting system: </label>
            <HTMLSelect
              name="cvrFileType"
              id="cvrFileType"
              value={selectedCvrFileType}
              onChange={e =>
                setSelectedCvrFileType(e.target.value as CvrFileType)
              }
              disabled={uploadDisabled || isUploading || cvrs.file !== null}
              style={{ width: '195px', marginLeft: '10px' }}
            >
              <option></option>
              <option value={CvrFileType.DOMINION}>Dominion</option>
              <option value={CvrFileType.CLEARBALLOT}>ClearBallot</option>
              <option value={CvrFileType.ESS}>ES&amp;S</option>
              <option value={CvrFileType.HART}>Hart</option>
            </HTMLSelect>
          </div>
        }
      />
    </>
  )
}
