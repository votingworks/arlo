import React, { useState, useEffect, useCallback } from 'react'
import { H1 } from '@blueprintjs/core'
import { Route, Switch } from 'react-router-dom'
import { IAuditFlowParams, IAudit, IAuditBoard } from '../../types'
import { api } from '../utilities'
import { statusStates } from '../AuditForms/_mocks'
import BoardTable from './BoardTable'
import MemberForm from './MemberForm'
import Ballot from './Ballot'
import Wrapper from '../Atoms/Wrapper'

const rand = (max: number = 100, min: number = 1) =>
  Math.floor(Math.random() * (+max - +min)) + +min

const dummyBoard: IAuditBoard[] = [
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
        position: '' + rand(2000),
        status: ['AUDITED', 'NOT_AUDITED'][rand(2, 0)] as
          | 'AUDITED'
          | 'NOT_AUDITED',
        vote: null,
        comment: '',
      })),
  },
]

interface IProps {
  match: {
    params: IAuditFlowParams
    url: string
  }
}

const AuditFlow: React.FC<IProps> = ({
  match: {
    params: { electionId, token },
    url,
  },
}: IProps) => {
  const [isLoading, setIsLoading] = useState<boolean>(false)

  const [audit, setAudit] = useState(statusStates[3])

  const getStatus = useCallback(async (): Promise<IAudit> => {
    const audit: IAudit = await api('/audit/status', { electionId })
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
    ...audit.jurisdictions[0].auditBoards.find(
      (v: IAuditBoard) => v.id === token
    ),
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
        <Switch>
          <Route
            exact
            path="/election/:electionId/board/:token"
            render={({ match: { url } }) => (
              <BoardTable
                isLoading={isLoading}
                setIsLoading={setIsLoading}
                board={board}
                url={url}
              />
            )}
          />
          <Route
            path={url + '/round/:roundId/ballot/:ballotId'}
            render={({
              match: {
                params: { roundId, ballotId },
              },
            }) => (
              <Ballot roundId={roundId} ballotId={ballotId} board={board} />
            )}
          />
        </Switch>
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
