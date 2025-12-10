import React, { useState } from 'react'
import {
  Card,
  RadioGroup,
  Radio,
  HTMLSelect,
  Callout,
  ButtonGroup,
  Button,
  Intent,
  Classes,
  H1,
} from '@blueprintjs/core'
import { useHistory, useLocation, Redirect } from 'react-router-dom'
import styled from 'styled-components'
import { Formik, FormikProps, Field } from 'formik'
import { useForm } from 'react-hook-form'
import { toast } from 'react-toastify'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import {
  useAuthDataContext,
  IJurisdictionAdmin,
  IElection,
  IOrganization,
  IAuditAdmin,
} from './UserContext'
import { parseApiError } from './utilities'
import LinkButton from './Atoms/LinkButton'
import FormSection from './Atoms/Form/FormSection'
import FormButton from './Atoms/Form/FormButton'
import { Wrapper, Inner } from './Atoms/Wrapper'
import FormField from './Atoms/Form/FormField'
import { groupBy, sortBy, partition } from '../utils/array'
import { IAuditSettings } from './useAuditSettings'
import { useConfirm, Confirm } from './Atoms/Confirm'
import { ErrorLabel } from './Atoms/Form/_helpers'
import { addCSRFToken, fetchApi } from '../utils/api'

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
            <AuditAdminHomeScreen user={user} />
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
    case 'tally_entry': {
      return <Redirect to="/tally-entry" />
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
  const {
    register: registerEmail,
    handleSubmit: handleSubmitEmail,
    errors: errorsEmail,
    setError: setErrorEmail,
  } = useForm<{
    email: string
  }>()
  const {
    register: registerCode,
    handleSubmit: handleSubmitCode,
    errors: errorsCode,
    setError: setErrorCode,
  } = useForm<{
    code: string
  }>()
  const [submittedEmail, setSubmittedEmail] = useState<string | null>(null)

  const onSubmitEmail = async ({ email }: { email: string }) => {
    const response = await fetch(
      '/auth/jurisdictionadmin/code',
      addCSRFToken({
        method: 'POST',
        headers: { 'Content-type': 'application/json' },
        body: JSON.stringify({ email }),
      })
    )
    if (response.ok) {
      setSubmittedEmail(email)
      return
    }

    const error = await parseApiError(response)
    if (response.status === 400)
      setErrorEmail('email', { message: error.message })
    else toast.error(error.message)
  }

  const onSubmitCode = async ({ code }: { code: string }) => {
    const response = await fetch(
      '/auth/jurisdictionadmin/login',
      addCSRFToken({
        method: 'POST',
        headers: { 'Content-type': 'application/json' },
        body: JSON.stringify({ email: submittedEmail, code }),
      })
    )
    if (response.ok) {
      window.location.reload()
      return
    }

    const error = await parseApiError(response)
    if (response.status === 400)
      setErrorCode('code', { message: error.message })
    else toast.error(error.message)
  }

  return (
    <LoginWrapper>
      <H1 style={{ fontSize: '2.5rem', marginBottom: '20px' }}>Arlo</H1>
      <div style={{ fontSize: '0.7rem' }}>
        <strong>Risk Limiting Audits by</strong>{' '}
        <img
          style={{ position: 'relative', bottom: '-4px' }}
          height="30px"
          src="/votingworks-logo.png"
          alt="Arlo, by VotingWorks"
        />
      </div>
      {query.get('error') && (
        <Callout intent="danger" style={{ margin: '20px 0 20px 0' }}>
          {query.get('message')}
        </Callout>
      )}
      <Card style={{ margin: '25px 0 15px 0' }}>
        {!submittedEmail ? (
          <form onSubmit={handleSubmitEmail(onSubmitEmail)}>
            <p>Participating in an audit in your local jurisdiction?</p>
            <label
              htmlFor="email"
              style={{ display: 'block', marginBottom: '10px' }}
            >
              <p>Enter your email to log in:</p>
              <input
                type="email"
                name="email"
                id="email"
                key="email"
                ref={registerEmail({ required: true })}
                className={`${Classes.INPUT} ${Classes.LARGE}`}
                style={{ width: '250px' }}
              />
            </label>
            {errorsEmail.email && (
              <ErrorLabel>{errorsEmail.email.message}</ErrorLabel>
            )}
            <Button type="submit" intent={Intent.PRIMARY} large>
              Log in to your audit
            </Button>
          </form>
        ) : (
          <>
            <form onSubmit={handleSubmitCode(onSubmitCode)}>
              <p>We sent an email with a login code to {submittedEmail}.</p>
              <label
                htmlFor="code"
                style={{ display: 'block', marginBottom: '10px' }}
              >
                <p>Enter the six-digit code below:</p>
                <input
                  type="text"
                  name="code"
                  id="code"
                  key="code"
                  ref={registerCode({ required: true })}
                  className={`${Classes.INPUT} ${Classes.LARGE}`}
                />
              </label>
              {errorsCode.code && (
                <ErrorLabel>{errorsCode.code.message}</ErrorLabel>
              )}
              <div>
                <Button onClick={() => setSubmittedEmail(null)} large>
                  Back
                </Button>
                <Button
                  type="submit"
                  intent={Intent.PRIMARY}
                  large
                  style={{ marginLeft: '5px' }}
                >
                  Submit code
                </Button>
              </div>
            </form>
          </>
        )}
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

const OrganizationAuditList = ({
  elections,
  onClickDeleteAudit,
}: {
  elections: IElection[]
  onClickDeleteAudit: (election: IElection) => void
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {sortBy(elections, election => new Date(election.createdAt).valueOf())
        .reverse()
        .map(election => (
          <ButtonGroup key={election.id} fill large>
            <LinkButton
              style={{ justifyContent: 'start' }}
              to={`/election/${election.id}`}
              intent={election.isComplete ? 'none' : 'primary'}
              fill
            >
              {election.auditName}
            </LinkButton>
            <Button
              icon="trash"
              intent={election.isComplete ? 'none' : 'primary'}
              aria-label="Delete Audit"
              onClick={() => onClickDeleteAudit(election)}
            />
          </ButtonGroup>
        ))}
    </div>
  )
}

const AuditAdminHomeScreen = ({ user }: { user: IAuditAdmin }) => {
  const queryClient = useQueryClient()
  const organizations = useQuery<IOrganization[]>('orgs', () =>
    fetchApi(`/api/audit_admins/${user.id}/organizations`)
  )
  const deleteElection = useMutation(
    ({ electionId }: { electionId: string }) =>
      fetchApi(`/api/election/${electionId}`, {
        method: 'DELETE',
      }),
    {
      onSuccess: () => queryClient.invalidateQueries('orgs'),
    }
  )
  const { confirm, confirmProps } = useConfirm()

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
      onYesClick: () => deleteElection.mutateAsync({ electionId: election.id }),
    })
  }

  if (!organizations.isSuccess) return null

  return (
    <>
      <div style={{ width: '50%', padding: '30px 30px 30px 0' }}>
        {sortBy(organizations.data, o => o.name).map(organization => {
          const [activeElections, completedElections] = partition(
            organization.elections,
            election => !election.isComplete
          )
          return (
            <div key={organization.id}>
              <div>
                <h2>Active Audits &mdash; {organization.name}</h2>
                {activeElections.length === 0 ? (
                  <p>You have no active audits at this time.</p>
                ) : (
                  <OrganizationAuditList
                    elections={activeElections}
                    onClickDeleteAudit={onClickDeleteAudit}
                  />
                )}
              </div>
              {completedElections.length > 0 && (
                <div>
                  <h2>Completed Audits &mdash; {organization.name}</h2>
                  <OrganizationAuditList
                    elections={completedElections}
                    onClickDeleteAudit={onClickDeleteAudit}
                  />
                </div>
              )}
            </div>
          )
        })}
        <Confirm {...confirmProps} />
      </div>
      <div style={{ width: '50%' }}>
        <CreateAudit organizations={organizations.data} />
      </div>
    </>
  )
}

const ListAuditsWrapper = styled.div`
  padding: 30px 30px 30px 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
`

const JurisdictionAuditList = ({
  auditJurisdictions,
}: {
  auditJurisdictions: [string, IJurisdictionAdmin['jurisdictions']][]
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {sortBy(auditJurisdictions, ([_, jurisdictions]) =>
        new Date(jurisdictions[0].election.createdAt).valueOf()
      )
        .reverse()
        .flatMap(([electionId, jurisdictions]) =>
          sortBy(jurisdictions, j => j.name).map(jurisdiction => (
            <LinkButton
              key={jurisdiction.id}
              to={`/election/${electionId}/jurisdiction/${jurisdiction.id}`}
              intent={jurisdiction.election.isComplete ? 'none' : 'primary'}
              large
              fill
              style={{ justifyContent: 'start' }}
            >
              {jurisdiction.name} &mdash; {jurisdiction.election.auditName}
            </LinkButton>
          ))
        )}
    </div>
  )
}

const ListAuditsJurisdictionAdmin = ({
  user,
}: {
  user: IJurisdictionAdmin
}) => {
  const jurisdictionsByAudit = groupBy(user.jurisdictions, j => j.election.id)
  const [activeAuditJurisdictions, completedAuditJurisdictions] = partition(
    Object.entries(jurisdictionsByAudit),
    ([_, jurisdictions]) => !jurisdictions[0].election.isComplete
  )

  return (
    <ListAuditsWrapper>
      <div>
        <h2>Active Audits</h2>
        {activeAuditJurisdictions.length === 0 ? (
          <p>You have no active audits at this time.</p>
        ) : (
          <JurisdictionAuditList
            key="active"
            auditJurisdictions={activeAuditJurisdictions}
          />
        )}
      </div>
      {completedAuditJurisdictions.length > 0 && (
        <div>
          <h2>Completed Audits</h2>
          <JurisdictionAuditList
            key="completed"
            auditJurisdictions={completedAuditJurisdictions}
          />
        </div>
      )}
    </ListAuditsWrapper>
  )
}

export interface INewAudit {
  organizationId: string
  auditName: string
  auditType: IAuditSettings['auditType']
  auditMathType: IAuditSettings['auditMathType']
}

const CreateAuditWrapper = styled.div`
  background-color: #ebf1f5;
  padding: 30px;
`

const MathTypeWrapper = styled.div`
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

const CreateAudit = ({ organizations }: { organizations: IOrganization[] }) => {
  const history = useHistory()
  const queryClient = useQueryClient()
  const createElection = useMutation<
    { electionId: string },
    unknown,
    INewAudit
  >(
    (newAudit: INewAudit) =>
      fetchApi('/api/election', {
        method: 'POST',
        body: JSON.stringify(newAudit),
        headers: {
          'Content-Type': 'application/json',
        },
      }),
    { onSuccess: () => queryClient.invalidateQueries('orgs') }
  )

  const onSubmit = async (newAudit: INewAudit) => {
    const { electionId } = await createElection.mutateAsync(newAudit)
    history.push(`/election/${electionId}/setup`)
  }

  return (
    <Formik
      onSubmit={onSubmit}
      initialValues={{
        organizationId: organizations[0].id,
        auditName: '',
        auditType: 'BALLOT_POLLING',
        auditMathType: 'BRAVO',
      }}
    >
      {({
        handleSubmit,
        isSubmitting,
        setFieldValue,
        setValues,
        values,
      }: FormikProps<INewAudit>) => (
        <CreateAuditWrapper>
          <h2>New Audit</h2>
          <FormSection>
            {/* eslint-disable jsx-a11y/label-has-associated-control */}
            {organizations.length > 1 && (
              <label htmlFor="organizationId">
                <p>Organization</p>
                <HTMLSelect
                  id="organizationId"
                  name="organizationId"
                  onChange={e =>
                    setFieldValue('organizationId', e.currentTarget.value)
                  }
                  value={values.organizationId}
                  options={organizations.map(({ id, name }) => ({
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
                disabled={isSubmitting}
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
                    .value as INewAudit['auditType']
                  const auditMathType = {
                    BALLOT_POLLING: 'BRAVO',
                    BALLOT_COMPARISON: 'SUPERSIMPLE',
                    BATCH_COMPARISON: 'MACRO',
                    HYBRID: 'SUITE',
                  }[auditType] as INewAudit['auditMathType']
                  setValues({ ...values, auditType, auditMathType })
                }}
                selectedValue={values.auditType}
              >
                <Radio value="BALLOT_POLLING">Ballot Polling</Radio>
                {values.auditType === 'BALLOT_POLLING' && (
                  <MathTypeWrapper>
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
                        <Radio value="MINERVA">Minerva (Beta)</Radio>
                      </RadioGroup>
                    </label>
                  </MathTypeWrapper>
                )}
                <Radio value="BATCH_COMPARISON">Batch Comparison</Radio>
                <Radio value="BALLOT_COMPARISON">Ballot Comparison</Radio>
                {values.auditType === 'BALLOT_COMPARISON' && (
                  <MathTypeWrapper>
                    <label htmlFor="auditMathType">
                      <p>Ballot comparison type</p>
                      <RadioGroup
                        name="auditMathType"
                        onChange={e =>
                          setFieldValue('auditMathType', e.currentTarget.value)
                        }
                        selectedValue={values.auditMathType}
                      >
                        <Radio value="SUPERSIMPLE">RCV (RAIRE)</Radio>
                        <Radio value="CARD_STYLE_DATA">
                          Card Style Data (Beta)
                        </Radio>
                      </RadioGroup>
                    </label>
                  </MathTypeWrapper>
                )}
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
            loading={isSubmitting}
          >
            Create Audit
          </FormButton>
        </CreateAuditWrapper>
      )}
    </Formik>
  )
}
