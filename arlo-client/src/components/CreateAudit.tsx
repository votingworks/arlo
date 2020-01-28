import React, { useState } from 'react'
import styled from 'styled-components'
import { toast } from 'react-toastify'
import { RouteComponentProps } from 'react-router-dom'
import FormButton from './Form/FormButton'
import { useAuth0, IAuth0Context } from '../react-auth0-spa'
import { api, checkAndToast } from './utilities'
import { ICreateAuditParams, IErrorResponse } from '../types'

export const Button = styled(FormButton)`
  margin: 65px 0;
`

export const Wrapper = styled.div`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  @media (min-width: 500px) {
    width: 400px;
  }
`

const CreateAudit = ({ history }: RouteComponentProps<ICreateAuditParams>) => {
  const [loading, setLoading] = useState(false)
  const { isAuthenticated, loginWithRedirect } = useAuth0() as IAuth0Context
  const onClick = async () => {
    try {
      setLoading(true)
      const response: { electionId: string } | IErrorResponse = await api(
        '/election/new',
        {
          method: 'POST',
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
      {isAuthenticated ? (
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
      ) : (
        <Button
          type="button"
          intent="primary"
          fill
          large
          onClick={() => loginWithRedirect({})}
          loading={loading}
          disabled={loading}
        >
          Welcome, Please Log In!
        </Button>
      )}
    </Wrapper>
  )
}

export default CreateAudit
