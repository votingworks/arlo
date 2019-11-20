import React, { useState } from 'react'
import styled from 'styled-components'
import { toast } from 'react-toastify'
import { RouteComponentProps } from 'react-router-dom'
import FormButton from './Form/FormButton'
import { api } from './utilities'
import { ICreateAuditParams } from '../types'

const Button = styled(FormButton)`
  margin: 65px 0;
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

const CreateAudit = ({ history }: RouteComponentProps<ICreateAuditParams>) => {
  const [loading, setLoading] = useState(false)
  const onClick = async () => {
    try {
      setLoading(true)
      const response: string = await api('/election/new', {
        method: 'POST',
      })
      const { electionId, errors } = JSON.parse(response)
      if (errors) {
        toast.error(
          'There was a server error regarding: ' +
            errors.map((v: { message: string }) => v.message).join(', ')
        )
      }
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
    </Wrapper>
  )
}

export default CreateAudit
