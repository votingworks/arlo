import React, { useState } from 'react'
import styled from 'styled-components'
import { toast } from 'react-toastify'
import { RouteComponentProps, Link } from 'react-router-dom'
import FormButton from './Form/FormButton'
import { api, checkAndToast } from './utilities'
import { ICreateAuditParams, IErrorResponse } from '../types'
import { useAuthDataContext } from './UserContext'

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

const CreateAudit = ({ history }: RouteComponentProps<ICreateAuditParams>) => {
  const { isAuthenticated, meta } = useAuthDataContext()

  const [loading, setLoading] = useState(false)
  const onClick = async () => {
    try {
      setLoading(true)
      const data = isAuthenticated
        ? // eslint-disable-next-line @typescript-eslint/camelcase
          { organization_id: meta!.organizations[0].id }
        : {}
      const response: { electionId: string } | IErrorResponse = await api(
        '/election/new',
        {
          method: 'POST',
          body: JSON.stringify(data),
        }
      )
      if (checkAndToast(response)) {
        return
      }
      const { electionId } = response
      history.push(`/election/${electionId}`)
    } catch (err) {
      toast.error(err.message)
    }
  }
  return (
    <Wrapper>
      <img height="50px" src="/arlo.png" alt="Arlo, by VotingWorks" />
      <Button
        type="button"
        intent="primary"
        fill
        large
        onClick={onClick}
        loading={loading}
        disabled={loading}
      >
        Create a New Audit
      </Button>
      {!isAuthenticated ? (
        <>
          <Button
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
                  {election.name || 'Not named yet'}
                  {election.state && ` (${election.state})`}
                </AuditLink>
              ))
            )}
          {meta!.jurisdictions.length > 0 &&
            meta!.jurisdictions.map(({ election }) => (
              <AuditLink
                to={`/election/${election.id}`}
                key={election.id}
                className="bp3-button bp3-intent-primary"
              >
                {election.name || 'Not named yet'}
                {election.state && ` (${election.state})`}
              </AuditLink>
            ))}
        </>
      )}
    </Wrapper>
  )
}

export default CreateAudit
