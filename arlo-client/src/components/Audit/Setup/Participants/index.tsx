/* eslint-disable jsx-a11y/label-has-associated-control */
import React, { useState } from 'react'
import { Formik, FormikProps, Form, Field, ErrorMessage } from 'formik'
import { useParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import styled from 'styled-components'
import { HTMLSelect, Spinner, FileInput } from '@blueprintjs/core'
import { IAudit, IErrorResponse } from '../../../../types'
import FormWrapper from '../../../Form/FormWrapper'
import FormButtonBar from '../../../Form/FormButtonBar'
import FormButton from '../../../Form/FormButton'
import { IValues } from './types'
import states from './states'
import schema from './schema'
import { ErrorLabel } from '../../../Form/_helpers'
import FormSection, { FormSectionDescription } from '../../../Form/FormSection'
import { api, checkAndToast } from '../../../utilities'

export const Select = styled(HTMLSelect)`
  margin-top: 5px;
`

const initialValues = {
  state: '',
  csv: null,
}

interface IProps {
  audit: IAudit
  nextStage: () => void
}

const Participants: React.FC<IProps> = ({ audit, nextStage }: IProps) => {
  const { electionId } = useParams()
  const [isLoading, setIsLoading] = useState(false)
  const submit = async (values: IValues) => {
    try {
      setIsLoading(true)
      /* istanbul ignore else */
      if (values.csv) {
        const formData: FormData = new FormData()
        formData.append('jurisdictions', values.csv, values.csv.name)
        const errorResponse: IErrorResponse = await api(
          `/election/${electionId}/jurisdictions/file`,
          {
            method: 'PUT',
            body: formData,
          }
        )
        if (checkAndToast(errorResponse)) return
      }
      nextStage()
    } catch (err) {
      toast.error(err.message)
    }
  }
  return (
    <Formik
      initialValues={initialValues}
      validationSchema={schema}
      onSubmit={submit}
    >
      {({
        handleSubmit,
        setFieldValue,
        values,
        touched,
        errors,
        handleBlur,
      }: FormikProps<IValues>) => (
        <Form data-testid="form-one">
          <FormWrapper title="Participants">
            <label htmlFor="state">
              Choose your state from the options below
              <br />
              <Field
                component={Select}
                id="state"
                data-testid="state-field"
                name="state"
                onChange={(e: React.FormEvent<HTMLSelectElement>) =>
                  setFieldValue('state', e.currentTarget.value)
                }
                disabled={!!audit.frozenAt}
                options={states}
              />
            </label>
            <ErrorMessage name="state" component={ErrorLabel} />
            {/* When one is already uploaded, this will be toggled to show its details, with a button to reveal the form to replace it */}
            <FormSection>
              <FormSectionDescription>
                Click &quot;Browse&quot; to choose the appropriate file from
                your computer. This file should be a comma-separated list of all
                the jurisdictions participating in the audit, plus email
                addresses for audit administrators in each participating
                jurisdiction.
                <br />
                <br />
                <a
                  href={`${window.location.origin}/sample_jurisdiction_filesheet.csv`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  (Click here to view a sample file in the correct format.)
                </a>
              </FormSectionDescription>
            </FormSection>
            <FormSection>
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
                text={values.csv ? values.csv.name : 'Select CSV...'}
                onBlur={handleBlur}
              />
              {errors.csv && touched.csv && (
                <ErrorLabel>{errors.csv}</ErrorLabel>
              )}
            </FormSection>
          </FormWrapper>
          {isLoading && <Spinner />}
          {!audit.contests.length && !isLoading && (
            <FormButtonBar>
              <FormButton
                type="submit"
                intent="primary"
                disabled={!!audit.frozenAt}
                onClick={handleSubmit}
              >
                Submit &amp; Next
              </FormButton>
            </FormButtonBar>
          )}
        </Form>
      )}
    </Formik>
  )
}

export default Participants
