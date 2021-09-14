/* eslint-disable jsx-a11y/label-has-associated-control */
import React, { useState } from 'react'
import { Formik, FormikProps } from 'formik'
import styled from 'styled-components'
import {
  HTMLSelect,
  FileInput,
  H4,
  ProgressBar,
  Intent,
} from '@blueprintjs/core'
import FormWrapper from '../../Atoms/Form/FormWrapper'
import FormButton from '../../Atoms/Form/FormButton'
import schema from './schema'
import { ErrorLabel, SuccessLabel } from '../../Atoms/Form/_helpers'
import FormSection, {
  FormSectionDescription,
} from '../../Atoms/Form/FormSection'
import { FileProcessingStatus, IFileInfo } from '../useCSV'
import AsyncButton from '../../Atoms/AsyncButton'

export const Select = styled(HTMLSelect)`
  margin-top: 5px;
`

interface IValues {
  csv: File | null
}

interface IProps {
  csvFile: IFileInfo
  uploadCSVFile: (csv: File) => Promise<boolean>
  deleteCSVFile?: () => Promise<boolean>
  title?: string
  description: string
  sampleFileLink: string
  enabled: boolean
}

const CSVFile = ({
  csvFile,
  uploadCSVFile,
  deleteCSVFile,
  title,
  description,
  sampleFileLink,
  enabled,
}: IProps) => {
  const { file, processing, upload } = csvFile
  const isProcessing = !!(processing && !processing.completedAt)
  const [isEditing, setIsEditing] = useState<boolean>(!file || isProcessing)

  return (
    <Formik
      enableReinitialize
      initialValues={{ csv: isProcessing ? new File([], file!.name) : null }}
      validationSchema={schema}
      validateOnBlur={false}
      onSubmit={async (values: IValues) => {
        if (values.csv) {
          await uploadCSVFile(values.csv)
          setIsEditing(false)
        }
      }}
    >
      {({
        handleSubmit,
        setFieldValue,
        values,
        touched,
        errors,
        handleBlur,
        isSubmitting,
      }: FormikProps<IValues>) => (
        <form>
          <FormWrapper>
            <FormSection>
              {title && <H4>{title}</H4>}
              <FormSectionDescription>
                {description}
                {sampleFileLink && (
                  <>
                    <br />
                    <br />
                    <a
                      href={sampleFileLink}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      (Click here to view a sample file in the correct format.)
                    </a>
                  </>
                )}
              </FormSectionDescription>
            </FormSection>
            {isEditing || !file || isProcessing ? (
              <>
                <FormSection>
                  <FileInput
                    inputProps={{
                      accept: '.csv',
                      name: 'csv',
                    }}
                    onInputChange={e =>
                      setFieldValue(
                        'csv',
                        (e.currentTarget.files && e.currentTarget.files[0]) ||
                          undefined
                      )
                    }
                    hasSelection={!!values.csv}
                    text={values.csv ? values.csv.name : 'Select a CSV...'}
                    onBlur={handleBlur}
                    disabled={isSubmitting || isProcessing || !enabled}
                  />
                  {errors.csv && touched.csv && (
                    <ErrorLabel>{errors.csv}</ErrorLabel>
                  )}
                  <div
                    style={{
                      display: 'flex',
                      marginTop: '15px',
                      marginBottom: '10px',
                      alignItems: 'center',
                      width: '300px',
                    }}
                  >
                    {isProcessing && (
                      <>
                        <span style={{ marginRight: '5px' }}>
                          Processing...
                        </span>
                        {processing!.workTotal && (
                          <ProgressBar
                            stripes={false}
                            intent={Intent.PRIMARY}
                            value={
                              processing!.workProgress! / processing!.workTotal
                            }
                          />
                        )}
                      </>
                    )}
                    {upload &&
                      // Only show upload progress for large files (over 1 MB),
                      // otherwise it will just flash on the screen
                      upload.file.size >= 1000 * 1000 && (
                        <>
                          <span style={{ marginRight: '5px' }}>
                            Uploading...
                          </span>
                          <ProgressBar
                            stripes={false}
                            intent={Intent.PRIMARY}
                            value={upload.progress}
                          />
                        </>
                      )}
                  </div>
                  <FormButton
                    type="submit"
                    intent="primary"
                    onClick={handleSubmit}
                    loading={isSubmitting || isProcessing}
                    disabled={!enabled}
                  >
                    Upload File
                  </FormButton>
                </FormSection>
              </>
            ) : (
              <>
                <FormSection>
                  <p>
                    <strong>Current file:</strong> {file.name}
                  </p>
                  {processing && processing.error && (
                    <ErrorLabel>{processing.error}</ErrorLabel>
                  )}
                  {processing &&
                    processing.status === FileProcessingStatus.PROCESSED && (
                      <SuccessLabel>
                        Uploaded at{' '}
                        {new Date(`${processing.completedAt}`).toLocaleString()}
                        .
                      </SuccessLabel>
                    )}
                  <div>
                    {/* We give these buttons a key to make sure React doesnt
                    reuse the submit button for one of them. */}
                    <FormButton
                      key="replace"
                      onClick={() => {
                        setFieldValue('csv', null)
                        setIsEditing(true)
                      }}
                      disabled={!enabled}
                    >
                      Replace File
                    </FormButton>
                    {deleteCSVFile && (
                      <AsyncButton
                        key="delete"
                        onClick={deleteCSVFile}
                        disabled={!enabled}
                        style={{ marginLeft: '5px' }}
                      >
                        Delete File
                      </AsyncButton>
                    )}
                  </div>
                </FormSection>
              </>
            )}
          </FormWrapper>
        </form>
      )}
    </Formik>
  )
}

export default CSVFile
