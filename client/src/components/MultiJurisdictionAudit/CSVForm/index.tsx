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
import { IFileInfo } from '../useJurisdictions'

export const Select = styled(HTMLSelect)`
  margin-top: 5px;
`

interface IValues {
  csv: File | null
}

interface IProps {
  csvFile: IFileInfo
  uploadCSVFile: (csv: File) => Promise<boolean>
  deleteCSVFile: () => Promise<boolean>
  title: string
  description: string
  sampleFileLink: string
  enabled: boolean
}

const CSVFile: React.FC<IProps> = (props: IProps) => {
  // Force the form to reset every time props.csvFile changes
  // E.g. if we upload or delete a file
  // See https://reactjs.org/blog/2018/06/07/you-probably-dont-need-derived-state.html#recap
  return <CSVFileForm key={Date.now()} {...props} />
}

const CSVFileForm = ({
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
      initialValues={{ csv: isProcessing ? new File([], file!.name) : null }}
      validationSchema={schema}
      onSubmit={async (values: IValues) => {
        if (values.csv) {
          await uploadCSVFile(values.csv)
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
              <H4>{title}</H4>
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
            <FormSection>
              {isEditing ? (
                <>
                  <FileInput
                    inputProps={{
                      accept: '.csv',
                      name: 'csv',
                    }}
                    onInputChange={e => {
                      setFieldValue(
                        'csv',
                        (e.currentTarget.files && e.currentTarget.files[0]) ||
                          undefined
                      )
                    }}
                    hasSelection={!!values.csv}
                    text={values.csv ? values.csv.name : 'Select a CSV...'}
                    onBlur={handleBlur}
                    disabled={isSubmitting || isProcessing || !enabled}
                  />
                  {errors.csv && touched.csv && (
                    <ErrorLabel>{errors.csv}</ErrorLabel>
                  )}
                </>
              ) : (
                <>
                  <p>
                    <strong>Current file:</strong> {file!.name}
                  </p>
                  {processing && processing.error && (
                    <ErrorLabel>{processing.error}</ErrorLabel>
                  )}
                  {processing && processing.completedAt && (
                    <SuccessLabel>
                      Upload successfully completed at{' '}
                      {new Date(`${processing.completedAt}Z`).toLocaleString()}!
                    </SuccessLabel>
                  )}
                </>
              )}
            </FormSection>
            <div>
              {isEditing ? (
                <FormButton
                  type="submit"
                  intent="primary"
                  onClick={handleSubmit}
                  loading={isSubmitting || isProcessing}
                  disabled={!enabled}
                >
                  Upload File
                </FormButton>
              ) : (
                // We give these buttons a key to make sure React doesn't reuse
                // the submit button for one of them.
                <>
                  <FormButton
                    key="replace"
                    onClick={() => setIsEditing(true)}
                    disabled={!enabled}
                  >
                    Replace File
                  </FormButton>
                  <FormButton
                    key="delete"
                    onClick={deleteCSVFile}
                    disabled={!enabled}
                  >
                    Delete File
                  </FormButton>
                </>
              )}
            </div>
          </FormWrapper>
        </form>
      )}
    </Formik>
  )
}

export default CSVFile
