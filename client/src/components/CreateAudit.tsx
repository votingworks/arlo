import React, { useState } from 'react'
import styled from 'styled-components'
import { RouteComponentProps, Link } from 'react-router-dom'
import { RadioGroup, Radio } from '@blueprintjs/core'
import { Formik, FormikProps, Field } from 'formik'
import FormButton from './Atoms/Form/FormButton'
import { api } from './utilities'
import { ICreateAuditParams, IAuditSettings } from '../types'
import { useAuthDataContext } from './UserContext'
import FormSection from './Atoms/Form/FormSection'
import FormField from './Atoms/Form/FormField'

const Button = styled(FormButton)`
  margin: 30px 0 0 0;
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

const AuditLink = styled(Link)`
  display: block;
  margin: 10px;

  &:first-of-type {
    margin-top: 30px;
  }
`

const CenterField = styled(FormField)`
  width: 100%;
`

const LeftRadioGroup = styled(RadioGroup)`
  padding: 20px;
  text-align: left;
`

interface IValues {
  auditName: string
  auditType: IAuditSettings['auditType']
}

const CreateAudit = ({ history }: RouteComponentProps<ICreateAuditParams>) => {
  const { isAuthenticated, meta } = useAuthDataContext()

  const [loading, setLoading] = useState(false)
  const onSubmit = async ({ auditName, auditType }: IValues) => {
    setLoading(true)
    const response = await api<{ electionId: string }>('/election/new', {
      method: 'POST',
      body: JSON.stringify({
        organizationId: meta!.organizations[0].id,
        auditName,
        auditType,
        isMultiJurisdiction: true,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    })
    if (!response) {
      setLoading(false)
      return
    }
    const { electionId } = response
    history.push(`/election/${electionId}/setup`)
  }

  if (isAuthenticated === null) return null // Still loading
  return (
    <Wrapper>
      <img height="50px" src="/arlo.png" alt="Arlo, by VotingWorks" />
      {isAuthenticated && meta!.type === 'audit_admin' && (
        <Formik
          onSubmit={onSubmit}
          initialValues={{ auditName: '', auditType: 'BALLOT_POLLING' }}
        >
          {({ handleSubmit, setFieldValue, values }: FormikProps<IValues>) => (
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
              <FormSection>
                <label htmlFor="auditType">
                  Audit type:
                  <LeftRadioGroup
                    name="auditType"
                    onChange={e =>
                      setFieldValue('auditType', e.currentTarget.value)
                    }
                    selectedValue={values.auditType}
                  >
                    <Radio value="BALLOT_POLLING">Ballot Polling</Radio>
                    <Radio value="BATCH_COMPARISON">Batch Comparison</Radio>
                  </LeftRadioGroup>
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
      )}
      {!isAuthenticated || (meta && meta.type === 'audit_board') ? (
        <>
          <Button
            verticalSpaced
            type="button"
            intent="primary"
            fill
            large
            onClick={
              /* istanbul ignore next */
              () => window.location.replace('/auth/auditadmin/start')
            }
            loading={loading}
            disabled={loading}
          >
            Log in as an Audit Admin
          </Button>
          <Button
            verticalSpaced
            type="button"
            intent="primary"
            fill
            large
            onClick={
              /* istanbul ignore next */
              () => window.location.replace('/auth/jurisdictionadmin/start')
            }
            loading={loading}
            disabled={loading}
          >
            Log in as a Jurisdiction Admin
          </Button>
        </>
      ) : (
        <>
          {meta!.organizations.length > 0 &&
            meta!.organizations.map(o =>
              o.elections.map(election => (
                <AuditLink
                  to={`/election/${election.id}`}
                  key={election.id}
                  className="bp3-button bp3-intent-primary"
                >
                  {election.auditName}
                  {election.state && ` (${election.state})`}
                </AuditLink>
              ))
            )}
          {meta!.jurisdictions.length > 0 &&
            meta!.jurisdictions.map(({ id, election }) => (
              <AuditLink
                to={`/election/${election.id}/jurisdiction/${id}`}
                key={election.id}
                className="bp3-button bp3-intent-primary"
              >
                {election.auditName}
                {election.state && ` (${election.state})`}
              </AuditLink>
            ))}
        </>
      )}
    </Wrapper>
  )
}

export default CreateAudit
