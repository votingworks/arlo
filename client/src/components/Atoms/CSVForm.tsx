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
import * as Yup from 'yup'
import { CvrFileType, IFileInfo, FileProcessingStatus } from '../useCSV'
import FormWrapper from './Form/FormWrapper'
import FormSection, { FormSectionDescription } from './Form/FormSection'
import { ErrorLabel, SuccessLabel } from './Form/_helpers'
import { sum } from '../../utils/number'
import FormButton from './Form/FormButton'
import AsyncButton from './AsyncButton'

export const Select = styled(HTMLSelect)`
  margin-top: 5px;
`

const schema = Yup.object().shape({
  csv: Yup.mixed().required('You must upload a file'),
})

interface IValues {
  csv: File[] | null
  cvrFileType?: CvrFileType
}

interface IProps {
  csvFile: IFileInfo
  uploadCSVFiles: (csvs: File[], cvrFileType?: CvrFileType) => Promise<boolean>
  deleteCSVFile?: () => Promise<boolean>
  title?: string
  description: string
  sampleFileLink?: string
  enabled: boolean
  showCvrFileType?: boolean
}

const CSVFile = ({
  csvFile,
  uploadCSVFiles,
  deleteCSVFile,
  title,
  description,
  sampleFileLink,
  enabled,
  showCvrFileType,
}: IProps) => {
  const { file, processing, upload } = csvFile
  const isProcessing = !!(processing && !processing.completedAt)
  const [isEditing, setIsEditing] = useState<boolean>(!file || isProcessing)

  return (
    <Formik
      initialValues={{
        csv: isProcessing ? [new File([], file!.name)] : null,
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
          await uploadCSVFiles(values.csv, values.cvrFileType)
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
            {showCvrFileType && (
              <div>
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
                    <option value={CvrFileType.HART}>Hart</option>
                  </HTMLSelect>
                </label>
              </div>
            )}
            {isEditing || !file || isProcessing ? (
              <>
                <FormSection>
                  <FileInput
                    inputProps={
                      values.cvrFileType === CvrFileType.HART
                        ? { accept: '.zip', name: 'zip' }
                        : {
                            accept: '.csv',
                            name: 'csv',
                            multiple: values.cvrFileType === CvrFileType.ESS,
                          }
                    }
                    onInputChange={e => {
                      const { files } = e.currentTarget
                      setFieldValue(
                        'csv',
                        files && files.length > 0 ? Array.from(files) : null
                      )
                    }}
                    hasSelection={!!values.csv}
                    text={(() => {
                      if (!values.csv) return 'Select a CSV...'
                      if (values.csv.length === 1) return values.csv[0].name
                      return `${values.csv.length} files selected`
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
                      sum(upload.files.map(f => f.size)) >= 1000 * 1000 && (
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
