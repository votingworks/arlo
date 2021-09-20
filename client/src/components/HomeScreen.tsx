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
} from './UserContext'
import { parseApiError, addCSRFToken } from './utilities'
import LinkButton from './Atoms/LinkButton'
import FormSection from './Atoms/Form/FormSection'
import FormButton from './Atoms/Form/FormButton'
import { Wrapper, Inner } from './Atoms/Wrapper'
import FormField from './Atoms/Form/FormField'
import { groupBy, sortBy } from '../utils/array'
import { IAuditSettings } from './MultiJurisdictionAudit/useAuditSettings'
import { useConfirm, Confirm } from './Atoms/Confirm'
import { ErrorLabel } from './Atoms/Form/_helpers'
import { fetchApi } from './SupportTools/support-api'

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
            <AuditAdminHomeScreen />
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
      <img height="50px" src="/arlo.png" alt="Arlo, by VotingWorks" />
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

const AuditAdminHomeScreen = () => {
  const queryClient = useQueryClient()
  const organizations = useQuery<IOrganization[]>('orgs', () =>
    fetchApi(`/api/organizations`)
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
        {sortBy(organizations.data, o => o.name).map(organization => (
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
      </div>
      <div style={{ width: '50%' }}>
        <CreateAudit organizations={organizations.data} />
      </div>
    </>
  )
}

const ListAuditsWrapper = styled.div`
  padding: 30px 30px 30px 0;
`

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

const CreateAudit = ({ organizations }: { organizations: IOrganization[] }) => {
  const history = useHistory()
  const createElection = useMutation<{ electionId: string }, unknown, IValues>(
    (newAudit: IValues) =>
      fetchApi('/api/election', {
        method: 'POST',
        body: JSON.stringify(newAudit),
        headers: {
          'Content-Type': 'application/json',
        },
      })
  )

  const onSubmit = async (newAudit: IValues) => {
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
      }: FormikProps<IValues>) => (
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
            loading={isSubmitting}
          >
            Create Audit
          </FormButton>
        </CreateAuditWrapper>
      )}
    </Formik>
  )
}
