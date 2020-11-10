import React, { useState, useEffect } from 'react'
import {
  Card,
  AnchorButton,
  RadioGroup,
  Radio,
  HTMLSelect,
  Callout,
} from '@blueprintjs/core'
import { useHistory, useLocation } from 'react-router-dom'
import styled from 'styled-components'
import { Formik, FormikProps, Field } from 'formik'
import { useAuthDataContext } from './UserContext'
import { api } from './utilities'
import { IAuditSettings, IUserMeta } from '../types'
import LinkButton from './Atoms/LinkButton'
import FormSection from './Atoms/Form/FormSection'
import FormButton from './Atoms/Form/FormButton'
import { Wrapper, Inner } from './Atoms/Wrapper'
import FormField from './Atoms/Form/FormField'
import { groupBy, sortBy } from '../utils/array'

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
              <ListAuditsAuditAdmin />
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
          <Inner>
            <div style={{ width: '50%' }}>
              <ListAuditsJurisdictionAdmin />
            </div>
          </Inner>
        </Wrapper>
      )
    case 'audit_board':
      return <LoginScreen />
    default:
      /* istanbul ignore next */
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
  // Support two query parameters: 'error' and 'message'
  // We use these to communicate authentication errors to the user.
  const query = new URLSearchParams(useLocation().search)

  return (
    <LoginWrapper>
      <img height="50px" src="/arlo.png" alt="Arlo, by VotingWorks" />
      {query.get('error') && (
        <Callout intent="danger" style={{ margin: '20px 0 20px 0' }}>
          {query.get('message')}
        </Callout>
      )}
      <Card style={{ margin: '25px 0 15px 0' }}>
        <p>Participating in an audit in your local jurisdiction?</p>
        <AnchorButton
          href="/auth/jurisdictionadmin/start"
          intent="primary"
          large
        >
          Log in to your audit
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
  padding: 30px 30px 30px 0;
`

const AuditLink = styled(LinkButton)`
  display: block;
  justify-content: start;
  margin-bottom: 15px;
`

const ListAuditsAuditAdmin: React.FC = () => {
  // Normally, we would use useAuthDataContext to get the audit admin's metadata
  // (including the list of audits). However, since this screen also is
  // responsible for creating audits, we need to make sure the list of audits
  // reloads when we create a new audit. So we load the user's data fresh every
  // time this component renders. It's a bit hacky and inefficient, but this is
  // the only screen that should have this issue. A better solution might be to
  // decouple loading the list of audits from loading the user data.
  const [meta, setMeta] = useState<IUserMeta | null>(null)

  useEffect(() => {
    ;(async () => {
      try {
        const userMeta: IUserMeta | null = await api('/me')
        setMeta(userMeta)
      } catch (err) /* istanbul ignore next */ {
        setMeta(null)
      }
    })()
  }, [])

  if (!meta) return null // Still loading

  return (
    <ListAuditsWrapper>
      {sortBy(meta.organizations, o => o.name).map(organization => (
        <div key={organization.id}>
          <h2>Audits - {organization.name}</h2>
          {organization.elections.length === 0 ? (
            <p>
              You haven&apos;t created any audits yet for {organization.name}
            </p>
          ) : (
            sortBy(organization.elections, e => e.auditName).map(election => (
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
    </ListAuditsWrapper>
  )
}

const ListAuditsJurisdictionAdmin: React.FC = () => {
  const { meta } = useAuthDataContext()
  const jurisdictionsByAudit = groupBy(meta!.jurisdictions, j => j.election.id)
  return (
    <ListAuditsWrapper>
      {sortBy(
        Object.entries(jurisdictionsByAudit),
        ([_, jurisdictions]) => jurisdictions[0].election.auditName
      ).map(([electionId, jurisdictions]) => (
        <div key={electionId}>
          <h2>Jurisdictions - {jurisdictions[0].election.auditName}</h2>
          {sortBy(jurisdictions, j => j.name).map(({ id, name, election }) => (
            <AuditLink
              key={id}
              to={`/election/${election.id}/jurisdiction/${id}`}
              intent="primary"
              large
              fill
            >
              {name}
            </AuditLink>
          ))}
        </div>
      ))}
    </ListAuditsWrapper>
  )
}

interface IValues {
  organizationId: string
  auditName: string
  auditType: IAuditSettings['auditType']
  auditMathType: IAuditSettings['auditMathType']
}

const CreateAuditWrapper = styled.div`
  background-color: #ebf1f5;
  padding: 30px;
`

const BallotPollingWrapper = styled.div`
  margin: 20px 0;
  background-color: #ffffff;
  padding-top: 10px;
  padding-bottom: 5px;
  padding-left: 20px;
  font-size: 85%;
`

const WideField = styled(FormField)`
  width: 100%;
`

const CreateAudit: React.FC = () => {
  const { meta } = useAuthDataContext()
  const history = useHistory()
  const [submitting, setSubmitting] = useState(false)

  const onSubmit = async ({
    organizationId,
    auditName,
    auditType,
    auditMathType,
  }: IValues) => {
    setSubmitting(true)
    const response: { electionId: string } | null = await api('/election', {
      method: 'POST',
      body: JSON.stringify({
        organizationId,
        auditName,
        auditType,
        auditMathType,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    })
    if (response) {
      const { electionId } = response
      history.push(`/election/${electionId}/setup`)
    } else {
      setSubmitting(false)
    }
  }
  return (
    <Formik
      onSubmit={onSubmit}
      initialValues={{
        organizationId: meta!.organizations[0].id,
        auditName: '',
        auditType: 'BALLOT_POLLING',
        auditMathType: 'BRAVO',
      }}
    >
      {({
        handleSubmit,
        setFieldValue,
        setValues,
        values,
      }: FormikProps<IValues>) => (
        <CreateAuditWrapper>
          <h2>New Audit</h2>
          <FormSection>
            {/* eslint-disable jsx-a11y/label-has-associated-control */}
            {meta!.organizations.length > 1 && (
              <label htmlFor="organizationId">
                <p>Organization</p>
                <HTMLSelect
                  id="organizationId"
                  name="organizationId"
                  onChange={e =>
                    setFieldValue('organizationId', e.currentTarget.value)
                  }
                  value={values.organizationId}
                  options={meta!.organizations.map(({ id, name }) => ({
                    label: name,
                    value: id,
                  }))}
                  fill
                />
              </label>
            )}
          </FormSection>
          <FormSection>
            <label htmlFor="auditName">
              <p>Audit name</p>
              <Field
                id="auditName"
                name="auditName"
                type="text"
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
                onChange={e => {
                  const auditType = e.currentTarget
                    .value as IValues['auditType']
                  const auditMathType = {
                    BALLOT_POLLING: 'BRAVO',
                    BALLOT_COMPARISON: 'SUPERSIMPLE',
                    BATCH_COMPARISON: 'MACRO',
                  }[auditType] as IValues['auditMathType']
                  setValues({ ...values, auditType, auditMathType })
                }}
                selectedValue={values.auditType}
              >
                <Radio value="BALLOT_POLLING">Ballot Polling</Radio>
                {/* For now, disable switching audit math type in production */}
                {process.env.REACT_APP_ENV !== 'production' &&
                values.auditType === 'BALLOT_POLLING' ? (
                  <BallotPollingWrapper>
                    <label htmlFor="auditMathType">
                      <p>Ballot polling type</p>
                      <RadioGroup
                        name="auditMathType"
                        onChange={e =>
                          setFieldValue('auditMathType', e.currentTarget.value)
                        }
                        selectedValue={values.auditMathType}
                      >
                        <Radio value="BRAVO">BRAVO</Radio>
                        <Radio value="MINERVA">Minerva (Not recommended)</Radio>
                      </RadioGroup>
                    </label>
                  </BallotPollingWrapper>
                ) : null}
                <Radio value="BATCH_COMPARISON">Batch Comparison</Radio>
                <Radio value="BALLOT_COMPARISON">Ballot Comparison</Radio>
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
