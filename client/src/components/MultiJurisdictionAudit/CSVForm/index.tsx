/* eslint-disable jsx-a11y/label-has-associated-control */
import React from 'react'
import styled from 'styled-components'
import {
  HTMLSelect,
  FileInput,
  H4,
  ProgressBar,
  Intent,
  Button,
} from '@blueprintjs/core'
import { ErrorLabel, SuccessLabel } from '../../Atoms/Form/_helpers'
import FormSection, {
  FormSectionDescription,
} from '../../Atoms/Form/FormSection'
import { IFileUpload, IFileUploadActions } from '../useCSV'
import AsyncButton from '../../Atoms/AsyncButton'

export const Select = styled(HTMLSelect)`
  margin-top: 5px;
`

const ButtonBar = styled.div`
  display: 'flex';
  align-items: 'center';
  margin-top: 15px;
  margin-bottom: 10px;
  width: 300px;
`

interface IProps {
  fileUpload: IFileUpload
  selectFile: IFileUploadActions['selectFile']
  uploadFile: IFileUploadActions['uploadFile']
  deleteFile?: IFileUploadActions['deleteFile']
  title?: string
  description: string
  sampleFileLink: string
  enabled: boolean
  showProgress?: boolean
}

// TODO form validation
const CSVFileForm = ({
  fileUpload,
  selectFile,
  uploadFile,
  deleteFile,
  title,
  description,
  sampleFileLink,
  enabled,
  showProgress,
}: IProps) => (
  <form style={{ maxWidth: '30rem' }}>
    <FormSection>
      {title && <H4>{title}</H4>}
      <FormSectionDescription>
        {description}
        {sampleFileLink && (
          <>
            <br />
            <br />
            <a href={sampleFileLink} target="_blank" rel="noopener noreferrer">
              (Click here to view a sample file in the correct format.)
            </a>
          </>
        )}
      </FormSectionDescription>
    </FormSection>
    <FormSection>
      <div style={{ width: '300px' }}>
        {(() => {
          switch (fileUpload.status) {
            case 'NO_FILE':
            case 'SELECTED':
              return (
                <>
                  <FileInput
                    inputProps={{ accept: '.csv' }}
                    onInputChange={e => {
                      selectFile(
                        (e.currentTarget.files && e.currentTarget.files[0]) ||
                          null
                      )
                    }}
                    hasSelection={fileUpload.status === 'SELECTED'}
                    text={
                      fileUpload.status === 'SELECTED'
                        ? fileUpload.clientFile.name
                        : 'Select a CSV...'
                    }
                    disabled={!enabled}
                    style={{ width: '100%' }}
                  />
                  <ButtonBar>
                    <Button
                      type="submit"
                      intent="primary"
                      onClick={() =>
                        fileUpload.status === 'SELECTED' &&
                        uploadFile(fileUpload.clientFile)
                      }
                      disabled={!enabled}
                    >
                      Upload File
                    </Button>
                  </ButtonBar>
                </>
              )
            case 'UPLOADING':
            case 'READY_TO_PROCESS':
            case 'PROCESSING':
              return (
                <>
                  <FileInput
                    hasSelection
                    text={
                      fileUpload.status === 'UPLOADING'
                        ? fileUpload.clientFile.name
                        : fileUpload.serverFile.file!.name
                    }
                    disabled
                    style={{ width: '100%' }}
                  />
                  <ButtonBar>
                    {showProgress && (
                      <div
                        style={{
                          marginBottom: '10px',
                          display: 'flex',
                          alignItems: 'center',
                        }}
                      >
                        <span style={{ marginRight: '5px' }}>
                          {fileUpload.status === 'UPLOADING'
                            ? 'Uploading...'
                            : 'Processing...'}
                        </span>
                        {fileUpload.status === 'UPLOADING' ? (
                          <ProgressBar
                            key="uploading"
                            stripes={false}
                            intent={Intent.PRIMARY}
                            value={fileUpload.uploadProgress}
                          />
                        ) : (
                          <ProgressBar
                            key="processing"
                            stripes={false}
                            intent={Intent.PRIMARY}
                            value={
                              fileUpload.serverFile.processing!.workTotal
                                ? fileUpload.serverFile.processing!
                                    .workProgress! /
                                  fileUpload.serverFile.processing!.workTotal
                                : 0
                            }
                          />
                        )}
                      </div>
                    )}
                    <Button intent="primary" loading>
                      Upload File
                    </Button>
                  </ButtonBar>
                </>
              )
            case 'PROCESSED':
            case 'ERRORED': {
              const {
                serverFile: { file, processing },
              } = fileUpload
              return (
                <>
                  <p>
                    <strong>Current file:</strong> {file!.name}
                  </p>
                  {fileUpload.status === 'ERRORED' && (
                    <ErrorLabel>{processing!.error}</ErrorLabel>
                  )}
                  {fileUpload.status === 'PROCESSED' && (
                    <SuccessLabel>
                      Upload completed at{' '}
                      {new Date(`${processing!.completedAt}`).toLocaleString()}.
                    </SuccessLabel>
                  )}
                  <ButtonBar>
                    {/* We give these buttons a key to make sure React doesn't
                  reuse the submit button for one of them. */}
                    <Button
                      key="replace"
                      onClick={() => selectFile(null)}
                      disabled={!enabled}
                    >
                      Replace File
                    </Button>
                    {deleteFile && (
                      <span style={{ marginLeft: '10px' }}>
                        <AsyncButton
                          key="delete"
                          onClick={deleteFile}
                          disabled={!enabled}
                        >
                          Delete File
                        </AsyncButton>
                      </span>
                    )}
                  </ButtonBar>
                </>
              )
            }
            default:
              return null
          }
        })()}
      </div>
    </FormSection>
  </form>
)

export default CSVFileForm
