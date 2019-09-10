import React, { useState, useEffect, useCallback } from 'react'
import styled from 'styled-components'
import { H1 } from '@blueprintjs/core'
import { AuditFlowParams, Audit, AuditBoard } from '../../types'
import { api } from '../utilities'
import { statusStates } from '../AuditForms/_mocks'
import BoardTable from './BoardTable'
import MemberForm from './MemberForm'

const rand = (max: number = 100, min: number = 1) =>
  Math.floor(Math.random() * (+max - +min)) + +min

const dummyBoard: AuditBoard[] = [
  {
    id: '123',
    name: 'Audit Board #1',
    members: [],
  },
  {
    id: '123',
    name: 'Audit Board #1',
    members: [
      {
        name: 'John Doe',
        affiliation: '',
      },
      {
        name: 'Jane Doe',
        affiliation: 'LIB',
      },
    ],
  },
  {
    id: '123',
    name: 'Audit Board #1',
    members: [
      {
        name: 'John Doe',
        affiliation: '',
      },
      {
        name: 'Jane Doe',
        affiliation: 'LIB',
      },
    ],
    ballots: Array(10)
      .fill('')
      .map(() => ({
        tabulator: '' + rand(),
        batch: `Precinct ${rand()}`,
        record: '' + rand(2000),
        status: ['AUDITED', 'NOT_AUDITED'][rand(2, 0)] as
          | 'AUDITED'
          | 'NOT_AUDITED',
        vote: ['YES', 'NO', 'NO_CONSENSUS', 'NO_VOTE', null][rand(5, 0)] as
          | 'YES'
          | 'NO'
          | 'NO_CONSENSUS'
          | 'NO_VOTE'
          | null,
      })),
  },
]

const Wrapper = styled.div`
  margin-top: 100px;
`

interface Props {
  match: {
    params: AuditFlowParams
  }
}

const AuditFlow: React.FC<Props> = ({
  match: {
    params: { electionId, token },
  },
}: Props) => {
  const [isLoading, setIsLoading] = useState<boolean>(false)

  const [audit, setAudit] = useState(statusStates[3])

  const getStatus = useCallback(async (): Promise<Audit> => {
    const audit: Audit = await api('/audit/status', { electionId })
    return audit
  }, [electionId])

  const updateAudit = useCallback(async () => {
    const audit = await getStatus()
    setIsLoading(true)
    setAudit(audit)
    setIsLoading(false)
  }, [getStatus])

  useEffect(() => {
    updateAudit()
  }, [updateAudit])

  const [dummy, setDummy] = useState(2)
  const board = {
    ...audit.jurisdictions[0].auditBoards.find(v => v.id === token),
    ...dummyBoard[dummy],
  }

  if (!board) {
    return (
      <Wrapper>
        <H1>
          Sorry, but that Audit Board does not exist in{' '}
          {audit.jurisdictions[0].name} and {audit.name}
        </H1>
      </Wrapper>
    )
  } else if (board.members.length) {
    return (
      <Wrapper>
        <BoardTable
          isLoading={isLoading}
          setIsLoading={setIsLoading}
          board={board}
        />
      </Wrapper>
    )
  } else {
    return (
      <Wrapper>
        <MemberForm
          isLoading={isLoading}
          setIsLoading={setIsLoading}
          setDummy={setDummy}
          boardName={board.name}
          jurisdictionName={audit.jurisdictions[0].name}
        />
      </Wrapper>
    )
  }
}

export default AuditFlow
