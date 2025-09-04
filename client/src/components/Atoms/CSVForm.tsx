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
  AnchorButton,
} from '@blueprintjs/core'
import * as Yup from 'yup'
import { CvrFileType, IFileInfo, FileProcessingStatus } from '../useCSV'
import FormWrapper from './Form/FormWrapper'
import { FormSectionDescription } from './Form/FormSection'
import { ErrorLabel, SuccessLabel } from './Form/_helpers'
import FormButton from './Form/FormButton'
import AsyncButton from './AsyncButton'

// CSVFile is deprecated in favor of FileUpload

export const Select = styled(HTMLSelect)`
  margin-top: 5px;
`

const schema = Yup.object().shape({
  csv: Yup.mixed().required('You must upload a file'),
})

interface IValues {
  csv: File | null
  cvrFileType?: CvrFileType
}

interface IProps {
  csvFile: IFileInfo
  uploadCSVFile: (csv: File, cvrFileType?: CvrFileType) => Promise<boolean>
  deleteCSVFile?: () => Promise<boolean>
  title?: string
  description: string
  sampleFileLink?: string
  enabled: boolean
  showCvrFileType?: boolean
}

const CSVFile: React.FC<IProps> = ({
  csvFile,
  uploadCSVFile,
  deleteCSVFile,
  title,
  description,
  sampleFileLink,
  enabled,
  showCvrFileType,
}) => {
  const { file, processing, upload } = csvFile
  const isProcessing = !!(processing && !processing.completedAt)
  const [isEditing, setIsEditing] = useState<boolean>(!file || isProcessing)

  return (
    <Formik
      initialValues={{
        csv: isProcessing ? new File([], file!.name) : null,
        cvrFileType: showCvrFileType
          ? file
            ? file.cvrFileType
            : CvrFileType.DOMINION
          : undefined,
      }}
      validationSchema={schema}
      validateOnChange={false}
      validateOnBlur={false}
      onSubmit={async (values: IValues) => {
        if (values.csv) {
          await uploadCSVFile(values.csv, values.cvrFileType)
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
            <div>
              {title && <H4>{title}</H4>}
              <FormSectionDescription>{description}</FormSectionDescription>
            </div>
            {showCvrFileType && (
              <p>
                <label>
                  <span style={{ marginRight: '5px' }}>CVR File Type:</span>
                  <HTMLSelect
                    value={values.cvrFileType}
                    disabled={!enabled || !(isEditing || !file)}
                    onChange={e => setFieldValue('cvrFileType', e.target.value)}
                  >
                    <option value={CvrFileType.DOMINION}>Dominion</option>
                    <option value={CvrFileType.CLEARBALLOT}>ClearBallot</option>
                    <option value={CvrFileType.ESS}>ES&amp;S</option>
                    <option value={CvrFileType.ESS_MD}>ES&amp;S (MD)</option>
                    <option value={CvrFileType.HART}>Hart</option>
                  </HTMLSelect>
                </label>
              </p>
            )}
            {isEditing || !file || isProcessing ? (
              <>
                <div>
                  <FileInput
                    inputProps={{
                      // While this component is named CSVFile, it can accept zip files in the case
                      // of Hart and ESS CVRs
                      // TODO: Consider renaming the component and its internals accordingly
                      accept:
                        values.cvrFileType &&
                        [
                          CvrFileType.HART,
                          CvrFileType.ESS,
                          CvrFileType.ESS_MD,
                        ].includes(values.cvrFileType)
                          ? '.zip'
                          : '.csv',
                      name: 'csv',
                    }}
                    onInputChange={e => {
                      const { files } = e.currentTarget
                      setFieldValue(
                        'csv',
                        files && files.length === 1 ? files[0] : null
                      )
                    }}
                    hasSelection={!!values.csv}
                    text={(() => {
                      if (!values.csv) {
                        return 'Select a file...'
                      }
                      return values.csv.name
                    })()}
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
                      // Only show upload progress for large sets of files (over 1 MB),
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
                  {sampleFileLink && (
                    <AnchorButton
                      href={sampleFileLink}
                      rel="noopener noreferrer"
                      style={{ marginLeft: '5px' }}
                      target="_blank"
                    >
                      Download Template
                    </AnchorButton>
                  )}
                </div>
              </>
            ) : (
              <>
                <div>
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
                        onClick={async () => {
                          await deleteCSVFile()
                          setFieldValue('csv', null)
                        }}
                        disabled={!enabled}
                        style={{ marginLeft: '5px' }}
                      >
                        Delete File
                      </AsyncButton>
                    )}
                    {sampleFileLink && (
                      <AnchorButton
                        href={sampleFileLink}
                        rel="noopener noreferrer"
                        style={{ marginLeft: '5px' }}
                        target="_blank"
                      >
                        Download Template
                      </AnchorButton>
                    )}
                  </div>
                </div>
              </>
            )}
          </FormWrapper>
        </form>
      )}
    </Formik>
  )
}

export default CSVFile
