/* eslint-disable jsx-a11y/label-has-associated-control */
import React, { useState } from 'react'
import { Formik, FormikProps, Form, Field, ErrorMessage } from 'formik'
import styled from 'styled-components'
import { HTMLSelect, Spinner } from '@blueprintjs/core'
import { IAudit } from '../../../../types'
import FormWrapper from '../../../Form/FormWrapper'
import FormButtonBar from '../../../Form/FormButtonBar'
import FormButton from '../../../Form/FormButton'
import { IValues } from './types'
import states from './states'
import schema from './schema'
import { ErrorLabel } from '../../../Form/_helpers'

export const Select = styled(HTMLSelect)`
  margin-top: 5px;
`

const initialValues = {
  state: '',
}

interface IProps {
  audit: IAudit
  nextStage: () => void
}

const Participants: React.FC<IProps> = ({ audit, nextStage }: IProps) => {
  const [isLoading, setIsLoading] = useState(false)
  return (
    <Formik
      initialValues={initialValues}
      validationSchema={schema}
      onSubmit={v => {
        setIsLoading(true)
        console.log(v)
        nextStage()
      }}
    >
      {({ handleSubmit, setFieldValue }: FormikProps<IValues>) => (
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
