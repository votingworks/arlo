import React from 'react'
import { H5, FileInput, Button, Colors, ProgressBar } from '@blueprintjs/core'
import { useForm } from 'react-hook-form'
import styled from 'styled-components'
import StatusTag, { StatusTagWithProgress } from './StatusTag'
import { IFileUpload } from '../useFileUpload'
import AsyncButton from './AsyncButton'

const ErrorDetails = styled.div.attrs({ className: 'bp3-text-small' })`
  margin-bottom: 10px;
  color: ${Colors.RED3};
`

export interface IFileUploadProps extends IFileUpload {
  title: string
  acceptFileTypes: ('csv' | 'zip')[]
  allowMultipleFiles?: boolean
  disabled?: boolean
  initialFile?: File
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
  disabled = false,
  initialFile,
}) => {
  const dataTransfer = new DataTransfer()
  if (initialFile) dataTransfer.items.add(initialFile)

  const { register, handleSubmit, formState, watch } = useForm<{
    files: FileList
  }>({
    mode: 'onTouched',
    defaultValues: {
      files: dataTransfer.files,
    },
  })

  if (!uploadedFile.isSuccess) return null

  const { file, processing } = uploadedFile.data

  const selectedFiles = watch('files')
  const numSelectedFiles = selectedFiles ? selectedFiles.length : 0

  const buttonAndTagWidth = '115px'
  const statusTagStyle = {
    width: buttonAndTagWidth,
    textAlign: 'center',
  }
  const statusTag = (() => {
    if (!uploadProgress && !file) return null //<StatusTag>No file uploaded</StatusTag>
    if (uploadProgress)
      return (
        <StatusTagWithProgress
          intent="warning"
          progress={uploadProgress}
          style={statusTagStyle}
        >
          Uploading
        </StatusTagWithProgress>
      )
    if (!processing || !file) return null // Impossible
    if (!processing.completedAt)
      return processing.workTotal ? (
        <StatusTagWithProgress
          intent="primary"
          progress={processing.workProgress! / processing.workTotal}
          style={statusTagStyle}
        >
          Processing
        </StatusTagWithProgress>
      ) : (
        <StatusTag intent="primary" style={statusTagStyle}>
          Processing
        </StatusTag>
      )
    if (processing?.error)
      return (
        <StatusTag intent="danger" style={statusTagStyle}>
          Upload Failed
        </StatusTag>
      )
    return (
      <StatusTag intent="success" style={statusTagStyle}>
        Uploaded
      </StatusTag>
    )
  })()

  const onUpload = async ({ files }: { files: FileList }) => {
    try {
      await uploadFiles(Array.from(files))
    } catch (error) {
      // Do nothing - toasting handled by queryClient
    }
  }

  return (
    <form onSubmit={handleSubmit(onUpload)} style={{ width: '400px' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '10px',
        }}
      >
        <H5 style={{ marginBottom: 0 }}>{title}</H5>
        {statusTag}
      </div>
      {processing?.error && <ErrorDetails>{processing.error}</ErrorDetails>}
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
        disabled={
          disabled ||
          formState.isSubmitting ||
          file !== null ||
          // TODO remove this last case
          uploadProgress !== undefined
        }
        fill
      />
      <div
        style={{
          marginTop: '10px',
          display: 'flex',
          justifyContent: 'flex-end',
          alignItems: 'center',
        }}
      >
        {!processing?.completedAt ? (
          <Button
            type="submit"
            intent="primary"
            icon="upload"
            disabled={
              disabled ||
              numSelectedFiles === 0 ||
              formState.isSubmitting ||
              (processing && !processing.completedAt) ||
              // TODO remove this last case
              uploadProgress !== undefined
            }
            style={{ width: buttonAndTagWidth }}
          >
            Upload
          </Button>
        ) : (
          <>
            <Button
              icon="download"
              style={{ marginRight: '5px', width: buttonAndTagWidth }}
            >
              Download
            </Button>
            <AsyncButton
              icon="delete"
              onClick={deleteFile}
              disabled={disabled}
              style={{ width: buttonAndTagWidth }}
            >
              Delete
            </AsyncButton>
          </>
        )}
      </div>
    </form>
  )

  // if (!uploadProgress && !file) {
  //   const onUpload = async ({ files }: { files: FileList }) => {
  //     try {
  //       await uploadFiles(Array.from(files))
  //     } catch (error) {
  //       // Do nothing - toasting handled by queryClient
  //     }
  //   }

  //   const files = watch('files')
  //   const numFiles = files ? files.length : 0

  //   return (
  //     <form onSubmit={handleSubmit(onUpload)}>
  //       <p>
  //         <StatusTag>No file uploaded</StatusTag>
  //       </p>
  //       <p>
  //         <FileInput
  //           inputProps={{
  //             accept: acceptFileTypes.map(fileType => `.${fileType}`).join(','),
  //             name: 'files',
  //             multiple: allowMultipleFiles,
  //             ref: register(),
  //           }}
  //           hasSelection={numFiles > 0}
  //           text={(() => {
  //             if (numFiles === 0)
  //               return allowMultipleFiles
  //                 ? 'Select files...'
  //                 : 'Select a file...'
  //             if (numFiles === 1) return files[0].name
  //             return `${numFiles} files selected`
  //           })()}
  //           disabled={disabled || formState.isSubmitting}
  //         />
  //       </p>
  //       <p>
  //         <Button
  //           type="submit"
  //           intent="primary"
  //           loading={formState.isSubmitting}
  //           disabled={disabled || numFiles === 0}
  //         >
  //           {allowMultipleFiles ? 'Upload Files' : 'Upload File'}
  //         </Button>
  //       </p>
  //     </form>
  //   )
  // }

  // if (uploadProgress) {
  //   return (
  //     <form>
  //       <p>
  //         <StatusTag intent="warning">Uploading</StatusTag>
  //       </p>
  //       <ProgressBar
  //         key="uploading"
  //         stripes={false}
  //         intent="warning"
  //         value={uploadProgress}
  //       />
  //     </form>
  //   )
  // }

  // /* istanbul ignore next */
  // if (!(file && processing)) {
  //   throw new Error('Invalid state')
  // }

  // if (!processing.completedAt) {
  //   return (
  //     <form>
  //       <p>
  //         <StatusTag intent="primary">Processing</StatusTag>
  //       </p>
  //       {processing.workTotal && (
  //         <ProgressBar
  //           key="processing"
  //           stripes={false}
  //           intent="primary"
  //           value={processing.workProgress! / processing.workTotal}
  //         />
  //       )}
  //     </form>
  //   )
  // }

  // const { error } = processing
  // return (
  //   <form>
  //     <p>
  //       {error ? (
  //         <StatusTag intent="danger">Upload failed</StatusTag>
  //       ) : (
  //         <StatusTag intent="success">Uploaded</StatusTag>
  //       )}
  //       <a
  //         href={downloadFileUrl}
  //         target="_blank"
  //         rel="noopener noreferrer"
  //         style={{ marginLeft: '15px' }}
  //       >
  //         {file.name}
  //       </a>
  //     </p>
  //     {error && <ErrorP>{error}</ErrorP>}
  //     <p>
  //       <AsyncButton disabled={disabled} onClick={deleteFile}>
  //         Delete File
  //       </AsyncButton>
  //     </p>
  //   </form>
  // )
}

export default FileUpload
