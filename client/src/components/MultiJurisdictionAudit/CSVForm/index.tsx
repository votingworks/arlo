/* eslint-disable jsx-a11y/label-has-associated-control */
import React, { useState } from 'react'
import { Formik, FormikProps } from 'formik'
import styled from 'styled-components'
import { HTMLSelect, FileInput, H4 } from '@blueprintjs/core'
import FormWrapper from '../../Atoms/Form/FormWrapper'
import FormButton from '../../Atoms/Form/FormButton'
import schema from './schema'
import { ErrorLabel, SuccessLabel } from '../../Atoms/Form/_helpers'
import FormSection, {
  FormSectionDescription,
} from '../../Atoms/Form/FormSection'
import { FileProcessingStatus, IFileInfo } from '../useCSV'

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
  const { file, processing } = csvFile
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
                </FormSection>

                <div>
                  <FormButton
                    type="submit"
                    intent="primary"
                    onClick={handleSubmit}
                    loading={isSubmitting || isProcessing}
                    disabled={!enabled}
                  >
                    Upload File
                  </FormButton>
                </div>
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
                        Upload successfully completed at{' '}
                        {new Date(`${processing.completedAt}`).toLocaleString()}
                        .
                      </SuccessLabel>
                    )}
                </FormSection>
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
                    <FormButton
                      key="delete"
                      onClick={async () => {
                        await deleteCSVFile()
                        setIsEditing(true)
                      }}
                      disabled={!enabled}
                    >
                      Delete File
                    </FormButton>
                  )}
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
