import React, { useState } from 'react'
import {
  Card,
  AnchorButton,
  RadioGroup,
  Radio,
  HTMLSelect,
} from '@blueprintjs/core'
import { useHistory } from 'react-router-dom'
import styled from 'styled-components'
import { Formik, FormikProps, Field } from 'formik'
import { toast } from 'react-toastify'
import { useAuthDataContext } from './UserContext'
import { api } from './utilities'
import { IAuditSettings } from '../types'
import LinkButton from './Atoms/LinkButton'
import FormSection from './Atoms/Form/FormSection'
import FormButton from './Atoms/Form/FormButton'
import { Wrapper, Inner } from './Atoms/Wrapper'
import FormField from './Atoms/Form/FormField'

const HomeScreen: React.FC = () => {
  const { isAuthenticated, meta } = useAuthDataContext()

  if (isAuthenticated === null) return null // Still loading

  if (!isAuthenticated) return <LoginScreen />

  switch (meta!.type) {
    case 'audit_admin':
      return (
        <Wrapper>
          <Inner>
            <div style={{ width: '50%' }}>
              <ListAudits />
            </div>
            <div style={{ width: '50%' }}>
              <CreateAudit />
            </div>
          </Inner>
        </Wrapper>
      )
    case 'jurisdiction_admin':
      return (
        <Wrapper>
          <ListAudits />
        </Wrapper>
      )
    case 'audit_board':
      return <LoginScreen />
    default:
      return null // Shouldn't happen
  }
}

export default HomeScreen

const LoginWrapper = styled.div`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  @media (min-width: 500px) {
    width: 400px;
  }
  text-align: center;
`

const LoginScreen: React.FC = () => {
  return (
    <LoginWrapper>
      <img height="50px" src="/arlo.png" alt="Arlo, by VotingWorks" />
      <Card style={{ margin: '25px 0 15px 0' }}>
        <p>Participating in an audit in your local jurisdiction?</p>
        <AnchorButton
          href="/auth/jurisdictionadmin/start"
          intent="primary"
          large
        >
          Log in to your jurisdiction
        </AnchorButton>
      </Card>
      <div>
        <p>
          State-level audit administrators:{' '}
          <a href="/auth/auditadmin/start">Log in as an admin</a>
        </p>
      </div>
    </LoginWrapper>
  )
}

const ListAuditsWrapper = styled.div`
  padding: 30px;
`

const AuditLink = styled(LinkButton)`
  display: block;
  justify-content: start;
  margin-bottom: 15px;
`

const ListAudits: React.FC = () => {
  const { meta } = useAuthDataContext()
  if (!meta) return null

  return (
    <ListAuditsWrapper>
      {meta.type === 'audit_admin' &&
        meta.organizations.map(organization => (
          <div key={organization.id}>
            <h2>Audits - {organization.name}</h2>
            {organization.elections.length === 0 ? (
              <p>
                You haven&apos;t created any audits yet for {organization.name}
              </p>
            ) : (
              organization.elections.map(election => (
                <AuditLink
                  key={election.id}
                  to={`/election/${election.id}`}
                  intent="primary"
                  large
                  fill
                >
                  {election.auditName}
                </AuditLink>
              ))
            )}
          </div>
        ))}
      {meta.type === 'jurisdiction_admin' &&
        meta.jurisdictions.map(({ id, name, election }) => (
          <AuditLink key={id} to={`/election/${election.id}`} intent="primary">
            {name} - {election.auditName}
          </AuditLink>
        ))}
    </ListAuditsWrapper>
  )
}

interface IValues {
  organizationId: string
  auditName: string
  auditType: IAuditSettings['auditType']
}

const CreateAuditWrapper = styled.div`
  background-color: #ebf1f5;
  padding: 30px;
`

const WideField = styled(FormField)`
  width: 100%;
`

const CreateAudit: React.FC = () => {
  const { meta } = useAuthDataContext()
  const history = useHistory()
  const [submitting, setSubmitting] = useState(false)

  if (!meta) return null

  const onSubmit = async ({
    organizationId,
    auditName,
    auditType,
  }: IValues) => {
    try {
      setSubmitting(true)
      const response: { electionId: string } = await api('/election/new', {
        method: 'POST',
        body: JSON.stringify({
          organizationId,
          auditName,
          auditType,
          isMultiJurisdiction: true,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      const { electionId } = response
      history.push(`/election/${electionId}/setup`)
    } catch (err) /* istanbul ignore next */ {
      // TODO move toasting into api
      toast.error(err.message)
      setSubmitting(false)
    }
  }
  return (
    <Formik
      onSubmit={onSubmit}
      initialValues={{
        organizationId: meta.organizations[0].id,
        auditName: '',
        auditType: 'BALLOT_POLLING',
      }}
    >
      {({ handleSubmit, setFieldValue, values }: FormikProps<IValues>) => (
        <CreateAuditWrapper>
          <h2>New Audit</h2>
          <FormSection>
            {/* eslint-disable jsx-a11y/label-has-associated-control */}
            {meta.organizations.length > 1 && (
              <label htmlFor="organizationId">
                <p>Organization</p>
                <HTMLSelect
                  name="organizationId"
                  onChange={e =>
                    setFieldValue('organizationId', e.currentTarget.value)
                  }
                  value={values.organizationId}
                  options={meta.organizations.map(({ id, name }) => ({
                    label: name,
                    value: id,
                  }))}
                  fill
                />
              </label>
            )}
          </FormSection>
          <FormSection>
            <label htmlFor="audit-name" id="audit-name-label">
              <p>Audit name</p>
              <Field
                id="audit-name"
                aria-labelledby="audit-name-label"
                name="auditName"
                disabled={submitting}
                validate={(v: string) => (v ? undefined : 'Required')}
                component={WideField}
              />
            </label>
          </FormSection>
          <FormSection>
            <label htmlFor="auditType">
              <p>Audit type</p>
              <RadioGroup
                name="auditType"
                onChange={e =>
                  setFieldValue('auditType', e.currentTarget.value)
                }
                selectedValue={values.auditType}
              >
                <Radio value="BALLOT_POLLING">Ballot Polling</Radio>
                <Radio value="BATCH_COMPARISON">Batch Comparison</Radio>
              </RadioGroup>
            </label>
          </FormSection>
          <FormButton
            type="button"
            intent="primary"
            fill
            large
            onClick={handleSubmit}
            loading={submitting}
          >
            Create Audit
          </FormButton>
        </CreateAuditWrapper>
      )}
    </Formik>
  )
}
