import React, { useState } from 'react'
import { toast } from 'react-toastify'
import { Formik, FormikProps, Field } from 'formik'
import { RouteComponentProps } from 'react-router-dom'
import styled from 'styled-components'
import FormSection from './components/Atoms/Form/FormSection'
import FormField from './components/Atoms/Form/FormField'
import { api } from './components/utilities'
import FormButton from './components/Atoms/Form/FormButton'

interface IValues {
  auditName: string
}

const Button = styled(FormButton)`
  margin: 30px 0 0 0;
`

const CenterField = styled(FormField)`
  width: 100%;
`

const Wrapper = styled.div`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  @media (min-width: 500px) {
    width: 400px;
  }
`

const CreateSingleJurisdictionAudit = ({ history }: RouteComponentProps) => {
  const [loading, setLoading] = useState(false)
  const onSubmit = async ({ auditName }: IValues) => {
    try {
      setLoading(true)
      const response: { electionId: string } = await api('/election/new', {
        method: 'POST',
        body: JSON.stringify({ auditName, isMultiJurisdiction: false }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      const { electionId } = response
      history.push(`/audit/${electionId}/setup`)
    } catch (err) /* istanbul ignore next */ {
      // will be removed when we migrate toasting to the api function
      toast.error(err.message)
      setLoading(false)
    }
  }
  return (
    <Wrapper>
      <img height="50px" src="/arlo.png" alt="Arlo, by VotingWorks" />
      <Formik onSubmit={onSubmit} initialValues={{ auditName: '' }}>
        {({ handleSubmit }: FormikProps<IValues>) => (
          <>
            <FormSection>
              {/* eslint-disable jsx-a11y/label-has-associated-control */}
              <label htmlFor="audit-name" id="audit-name-label">
                Give your new audit a unique name.
                <Field
                  id="audit-name"
                  aria-labelledby="audit-name-label"
                  name="auditName"
                  disabled={loading}
                  validate={(v: string) => (v ? undefined : 'Required')}
                  component={CenterField}
                />
              </label>
            </FormSection>
            <Button
              type="button"
              intent="primary"
              fill
              large
              onClick={handleSubmit}
              loading={loading}
              disabled={loading}
            >
              Create a New Audit
            </Button>
          </>
        )}
      </Formik>
    </Wrapper>
  )
}

export default CreateSingleJurisdictionAudit
