import React, { useState, useEffect } from 'react'
import {
  Card,
  AnchorButton,
  RadioGroup,
  Radio,
  HTMLSelect,
  Callout,
  ButtonGroup,
  Button,
  Intent,
} from '@blueprintjs/core'
import { useHistory, useLocation, Redirect } from 'react-router-dom'
import styled from 'styled-components'
import { Formik, FormikProps, Field } from 'formik'
import {
  useAuthDataContext,
  IAuditAdmin,
  IJurisdictionAdmin,
  IElection,
} from './UserContext'
import { api } from './utilities'
import LinkButton from './Atoms/LinkButton'
import FormSection from './Atoms/Form/FormSection'
import FormButton from './Atoms/Form/FormButton'
import { Wrapper, Inner } from './Atoms/Wrapper'
import FormField from './Atoms/Form/FormField'
import { groupBy, sortBy } from '../utils/array'
import { IAuditSettings } from './MultiJurisdictionAudit/useAuditSettings'
import { useConfirm, Confirm } from './Atoms/Confirm'

const HomeScreen: React.FC = () => {
  const auth = useAuthDataContext()

  if (auth === null) return null // Still loading

  const { user } = auth
  if (!user) return <LoginScreen />

  switch (user.type) {
    case 'audit_admin':
      return (
        <Wrapper>
          <Inner>
            <div style={{ width: '50%' }}>
              <ListAuditsAuditAdmin />
            </div>
            <div style={{ width: '50%' }}>
              <CreateAudit user={user} />
            </div>
          </Inner>
        </Wrapper>
      )
    case 'jurisdiction_admin': {
      if (user.jurisdictions.length === 1) {
        const electionId = user.jurisdictions[0].election.id
        const jurisdictionId = user.jurisdictions[0].id
        return (
          <Redirect
            to={`election/${electionId}/jurisdiction/${jurisdictionId}`}
          />
        )
      }

      return (
        <Wrapper>
          <Inner>
            <div style={{ width: '50%' }}>
              <ListAuditsJurisdictionAdmin user={user} />
            </div>
          </Inner>
        </Wrapper>
      )
    }
    case 'audit_board': {
      const { electionId, id: auditBoardId } = user
      const auditBoardUrl = `/election/${electionId}/audit-board/${auditBoardId}`
      return <Redirect to={auditBoardUrl} />
    }
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

const ListAuditsAuditAdmin: React.FC = () => {
  // Normally, we would use useAuthDataContext to get the audit admin's metadata
  // (including the list of audits). However, since this screen also is
  // responsible for creating audits, we need to make sure the list of audits
  // reloads when we create a new audit. So we load the user's data fresh every
  // time this component renders. It's a bit hacky and inefficient, but this is
  // the only screen that should have this issue. A better solution might be to
  // decouple loading the list of audits from loading the user data.
  const [user, setUser] = useState<IAuditAdmin | null>(null)
  const { confirm, confirmProps } = useConfirm()

  const loadUser = async () => {
    const response = await api<{ user: IAuditAdmin }>('/me')
    setUser(response && response.user)
  }

  useEffect(() => {
    loadUser()
  }, [])

  if (!user) return null // Still loading

  const onClickDeleteAudit = (election: IElection) => {
    confirm({
      title: 'Confirm',
      description: (
        <div>
          <p>Are you sure you want to delete {election.auditName}?</p>
          <p>
            <strong>Warning: this action cannot be undone.</strong>
          </p>
        </div>
      ),
      yesButtonLabel: 'Delete',
      yesButtonIntent: Intent.DANGER,
      onYesClick: async () => {
        await api(`/election/${election.id}`, { method: 'DELETE' })
        await loadUser()
      },
    })
  }

  return (
    <ListAuditsWrapper>
      {sortBy(user.organizations, o => o.name).map(organization => (
        <div key={organization.id}>
          <h2>Audits - {organization.name}</h2>
          {organization.elections.length === 0 ? (
            <p>
              You haven&apos;t created any audits yet for {organization.name}
            </p>
          ) : (
            sortBy(organization.elections, e => e.auditName).map(election => (
              <ButtonGroup
                key={election.id}
                fill
                large
                style={{ marginBottom: '15px' }}
              >
                <LinkButton
                  style={{ justifyContent: 'start' }}
                  to={`/election/${election.id}`}
                  intent="primary"
                  fill
                >
                  {election.auditName}
                </LinkButton>
                <Button
                  icon="trash"
                  intent="primary"
                  aria-label="Delete Audit"
                  onClick={() => onClickDeleteAudit(election)}
                />
              </ButtonGroup>
            ))
          )}
        </div>
      ))}
      <Confirm {...confirmProps} />
    </ListAuditsWrapper>
  )
}

const ListAuditsJurisdictionAdmin = ({
  user,
}: {
  user: IJurisdictionAdmin
}) => {
  const jurisdictionsByAudit = groupBy(user.jurisdictions, j => j.election.id)
  return (
    <ListAuditsWrapper>
      {Object.entries(jurisdictionsByAudit).length === 0 ? (
        <Callout intent="warning">
          You don&apos;t have any available audits at the moment
        </Callout>
      ) : (
        sortBy(
          Object.entries(jurisdictionsByAudit),
          ([_, jurisdictions]) => jurisdictions[0].election.auditName
        ).map(([electionId, jurisdictions]) => (
          <div key={electionId}>
            <h2>Jurisdictions - {jurisdictions[0].election.auditName}</h2>
            {sortBy(jurisdictions, j => j.name).map(
              ({ id, name, election }) => (
                <LinkButton
                  key={id}
                  to={`/election/${election.id}/jurisdiction/${id}`}
                  intent="primary"
                  large
                  fill
                  style={{
                    justifyContent: 'start',
                    marginBottom: '15px',
                  }}
                >
                  {name}
                </LinkButton>
              )
            )}
          </div>
        ))
      )}
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

const CreateAudit = ({ user }: { user: IAuditAdmin }) => {
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
        organizationId: user.organizations[0].id,
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
            {user.organizations.length > 1 && (
              <label htmlFor="organizationId">
                <p>Organization</p>
                <HTMLSelect
                  id="organizationId"
                  name="organizationId"
                  onChange={e =>
                    setFieldValue('organizationId', e.currentTarget.value)
                  }
                  value={values.organizationId}
                  options={user.organizations.map(({ id, name }) => ({
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
                    HYBRID: 'SUITE',
                  }[auditType] as IValues['auditMathType']
                  setValues({ ...values, auditType, auditMathType })
                }}
                selectedValue={values.auditType}
              >
                <Radio value="BALLOT_POLLING">Ballot Polling</Radio>
                {values.auditType === 'BALLOT_POLLING' && (
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
                )}
                <Radio value="BATCH_COMPARISON">Batch Comparison</Radio>
                <Radio value="BALLOT_COMPARISON">Ballot Comparison</Radio>
                <Radio value="HYBRID">
                  Hybrid (SUITE - Ballot Comparison &amp; Ballot Polling)
                </Radio>
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
