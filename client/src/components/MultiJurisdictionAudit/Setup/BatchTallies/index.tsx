/* eslint-disable jsx-a11y/label-has-associated-control */
import React, { useState } from 'react'
import { Formik, FormikProps, Form } from 'formik'
import styled from 'styled-components'
import { HTMLSelect, FileInput, H4 } from '@blueprintjs/core'
import FormWrapper from '../../../Atoms/Form/FormWrapper'
import FormButton from '../../../Atoms/Form/FormButton'
import schema from './schema'
import { ErrorLabel } from '../../../Atoms/Form/_helpers'
import FormSection, {
  FormSectionDescription,
} from '../../../Atoms/Form/FormSection'
import { IFileInfo } from '../../useJurisdictions'

export const Select = styled(HTMLSelect)`
  margin-top: 5px;
`

interface IValues {
  csv: File | null
}

interface IProps {
  batchTallies: IFileInfo
  enabled: boolean
  uploadBatchTallies: (csv: File) => Promise<boolean>
  deleteBatchTallies: () => Promise<boolean>
}

const BatchTallies: React.FC<IProps> = (props: IProps) => {
  // Force the form to reset every time props.batchTallies changes
  // E.g. if we upload or delete a file
  // See https://reactjs.org/blog/2018/06/07/you-probably-dont-need-derived-state.html#recap
  return <BatchTalliesForm key={Date.now()} {...props} />
}

const BatchTalliesForm = ({
  batchTallies,
  enabled,
  uploadBatchTallies,
  deleteBatchTallies,
}: IProps) => {
  const { file, processing } = batchTallies
  const isProcessing = !!(processing && !processing.completedAt)
  const [isEditing, setIsEditing] = useState<boolean>(!file || isProcessing)

  return (
    <Formik
      initialValues={{ csv: null }}
      validationSchema={schema}
      onSubmit={async (values: IValues) => {
        if (values.csv) {
          uploadBatchTallies(values.csv)
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
      }: FormikProps<IValues>) => (
        <Form>
          <FormWrapper>
            <H4>Candidate Totals by Batch</H4>
            <FormSection>
              <FormSectionDescription>
                Click &quot;Browse&quot; to choose the appropriate Candidate
                Totals by Batch file from your computer. This file should be a
                comma-separated list of all the ballot boxes/containers used to
                store ballots for this particular election, plus a count of how
                many votes were counted for each candidate in each of those
                containers.
                <br />
                <br />
                <a
                  href={`${window.location.origin}/sample_batch_tallies.csv`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  (Click here to view a sample file in the correct format.)
                </a>
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
                    disabled={isProcessing || !enabled}
                  />
                  {errors.csv && touched.csv && (
                    <ErrorLabel>{errors.csv}</ErrorLabel>
                  )}
                </>
              ) : (
                <>
                  <p>
                    <strong>Current Batch Tallies file:</strong> {file!.name}
                  </p>
                  {processing && processing.error && (
                    <ErrorLabel>{processing.error}</ErrorLabel>
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
                  loading={isProcessing}
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
                    onClick={deleteBatchTallies}
                    disabled={!enabled}
                  >
                    Delete File
                  </FormButton>
                </>
              )}
            </div>
          </FormWrapper>
        </Form>
      )}
    </Formik>
  )
}

export default BatchTallies
