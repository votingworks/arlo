import React, { useState, useEffect, useCallback } from 'react'
import { H1 } from '@blueprintjs/core'
import { Route, Switch } from 'react-router-dom'
import { History } from 'history'
import { IAuditFlowParams, IAudit, IAuditBoard } from '../../types'
import { api } from '../utilities'
import { statusStates } from '../AuditForms/_mocks'
import { dummyBoard } from './_mocks'
import BoardTable from './BoardTable'
import MemberForm from './MemberForm'
import Ballot from './Ballot'
import Wrapper from '../Atoms/Wrapper'

interface IProps {
  match: {
    params: IAuditFlowParams
    url: string
  }
  history: History
  dummyID?: number
}

const AuditFlow: React.FC<IProps> = ({
  match: {
    params: { electionId, token },
    url,
  },
  history,
  dummyID = 2,
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

  const [dummy, setDummy] = useState(dummyID)
  const board = {
    ...audit.jurisdictions[0].auditBoards.find(
      (v: IAuditBoard) => v.id === token
    ),
    ...dummyBoard[dummy],
  }

  const nextBallot = (r: string, b: string) => () => {
    history.push(`${url}/round/${r}/ballot/${Number(b) + 1}`)
  }

  const previousBallot = (r: string, b: string) => () => {
    history.push(`${url}/round/${r}/ballot/${Number(b) - 1}`)
  }

  /* istanbul ignore if */
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
              <Ballot
                home={url}
                previousBallot={previousBallot(roundId, ballotId)}
                nextBallot={nextBallot(roundId, ballotId)}
                contest={audit.contests[0].name}
                roundId={roundId}
                ballotId={ballotId}
                board={board}
              />
            )}
          />
        </Switch>
      </Wrapper>
    )
  } else {
    return (
      <Wrapper>
        <MemberForm
          setDummy={setDummy}
          boardName={board.name}
          jurisdictionName={audit.jurisdictions[0].name}
        />
      </Wrapper>
    )
  }
}

export default AuditFlow
