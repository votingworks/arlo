import React, { useState, useEffect, useCallback } from 'react'
import styled from 'styled-components'
import { toast } from 'react-toastify'
import { RouteComponentProps } from 'react-router-dom'
import FormButton from './Form/FormButton'
import { api, checkAndToast } from './utilities'
import { ICreateAuditParams, IErrorResponse } from '../types'

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

interface IElection {
  id: string
  name: string
  date: string
}
interface IElections {
  elections: IElection[]
}

const CreateAudit = ({ history }: RouteComponentProps<ICreateAuditParams>) => {
  const [loading, setLoading] = useState(false)
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

  const [elections, setElections] = useState<IElections>({ elections: [] })

  const getStatus = useCallback(async (): Promise<IElections> => {
    const list: IElections | IErrorResponse = await api(`/elections`)
    if (checkAndToast(list)) {
      return { elections: [] }
    } else {
      return list
    }
  }, [])

  const updateElections = useCallback(async () => {
    const list = await getStatus()
    setLoading(true)
    setElections(list)
    setLoading(false)
  }, [getStatus])

  useEffect(() => {
    updateElections()
  }, [updateElections])

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
      <div>
        {elections.elections.map(e => (
          <div key={e.id}>
            {e.name} ({e.date})
          </div>
        ))}
      </div>
    </Wrapper>
  )
}

export default CreateAudit
