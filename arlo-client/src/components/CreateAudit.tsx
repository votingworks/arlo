import React, { useState, useEffect, useCallback } from 'react'
import styled from 'styled-components'
import moment from 'moment'
import { toast } from 'react-toastify'
import { RouteComponentProps, Link } from 'react-router-dom'
import { RadioGroup, Radio } from '@blueprintjs/core'
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
export interface IElections {
  elections: IElection[]
}

const CreateAudit = ({ history }: RouteComponentProps<ICreateAuditParams>) => {
  const [loading, setLoading] = useState(false)
  const [electionId, setElectionId] = useState('')

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
    try {
      const list: IElections | IErrorResponse = await api(`/elections`)
      if (checkAndToast(list)) {
        return { elections: [] }
      } else {
        return list
      }
    } catch (err) {
      toast.error(err.message)
    }
    return { elections: [] }
  }, [])

  const updateElections = useCallback(async () => {
    const list = await getStatus()
    setLoading(true)
    setElections(list)
    setElectionId(list.elections.length ? list.elections[0].id : '')
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
      {elections.elections.length > 0 ? (
        <>
          <RadioGroup
            label="Select an existing audit:"
            selectedValue={electionId}
            onChange={e => setElectionId(e.currentTarget.value)}
          >
            {elections.elections.map(e => (
              <Radio key={e.id} value={e.id}>
                {e.name || <i>Not named yet</i>} (Created&nbsp;
                {moment(e.date).format('MM/DD/YYYY')})
              </Radio>
            ))}
          </RadioGroup>
          <Link
            to={`/election/${electionId}`}
            className="bp3-button bp3-intent-primary"
          >
            View Audit
          </Link>
        </>
      ) : (
        <p>
          You do not have any audits currently associated with your account.
        </p>
      )}
    </Wrapper>
  )
}

export default CreateAudit
