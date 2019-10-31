import React, { useState, useEffect, useCallback } from 'react'
import { Spinner } from '@blueprintjs/core'
import { Route, Switch } from 'react-router-dom'
import { History } from 'history'
import { toast } from 'react-toastify'
import { IAuditFlowParams, IAudit, IAuditBoard, IBallot } from '../../types'
import { api, poll } from '../utilities'
import { statusStates } from '../AuditForms/_mocks'
import {
  // dummyBoard,
  dummyBallots,
} from './_mocks'
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
}

const AuditFlow: React.FC<IProps> = ({
  match: {
    params: { electionId, token },
    url,
  },
  history,
}: IProps) => {
  const [isLoading, setIsLoading] = useState<boolean>(false)

  const [audit, setAudit] = useState(statusStates[3])

  const getStatus = useCallback(async (): Promise<IAudit> => {
    const audit: IAudit = await api('/audit/status', { electionId })
    return audit
  }, [electionId])

  const updateAudit = useCallback(async () => {
    setIsLoading(true)
    const audit = await getStatus()
    setAudit(audit)
    setIsLoading(false)
  }, [getStatus])

  useEffect(() => {
    updateAudit()
  }, [updateAudit])

  const board:
    | IAuditBoard
    | undefined = audit.jurisdictions[0].auditBoards.find(
    (v: IAuditBoard) => v.id === token
  )

  const round = audit.rounds[audit.rounds.length - 1]

  const [ballots, setBallots] = useState<IBallot[]>(dummyBallots.ballots)

  const getBallots = useCallback(async (): Promise<IBallot[]> => {
    if (audit.jurisdictions.length && board) {
      const { ballots } = await api(
        `/jurisdiction/${audit.jurisdictions[0].id}/audit-board/${board.id}/round/${round.id}/ballot-list`,
        { electionId }
      )
      return ballots
    } else {
      return []
    }
  }, [electionId, audit.jurisdictions, round, board])

  const updateBallots = useCallback(async () => {
    setIsLoading(true)
    let ballots: IBallot[] = []
    poll(
      async () => {
        ballots = await getBallots()
        return !!ballots.length
      },
      () => setBallots(ballots),
      (err: Error) => toast.error(err.message)
    )
    setIsLoading(false)
  }, [getBallots])

  useEffect(() => {
    updateBallots()
  }, [updateBallots, audit.jurisdictions.length])

  const nextBallot = (r: string, batchId: string, ballot: number) => () => {
    const ballotIx = ballots.findIndex(
      (b: IBallot) => b.batch.id === batchId && b.position === ballot
    )
    if (ballotIx > -1 && ballots[ballotIx + 1]) {
      const b = ballots[ballotIx + 1]
      history.push(`${url}/round/${r}/batch/${b.batch.id}/ballot/${b.position}`)
    } else {
      history.push(url)
    }
  }

  const previousBallot = (r: string, batchId: string, ballot: number) => () => {
    const ballotIx = ballots.findIndex(
      (b: IBallot) => b.batch.id === batchId && b.position === ballot
    )
    if (ballotIx > -1 && ballots[ballotIx - 1]) {
      const b = ballots[ballotIx - 1]
      history.push(`${url}/round/${r}/batch/${b.batch.id}/ballot/${b.position}`)
    } else {
      history.push(url)
    }
  }

  /* istanbul ignore if */
  if (!board) {
    return (
      <Wrapper>
        <Spinner />
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
                boardName={board.name}
                ballots={ballots}
                round={audit.rounds.length}
                url={url}
              />
            )}
          />
          <Route
            path={url + '/round/:roundId/batch/:batchId/ballot/:ballotId'}
            render={({
              match: {
                params: { roundId, batchId, ballotId },
              },
            }) => (
              <Ballot
                home={url}
                previousBallot={previousBallot(
                  roundId,
                  batchId,
                  Number(ballotId)
                )}
                nextBallot={nextBallot(roundId, batchId, Number(ballotId))}
                contest={audit.contests[0].name}
                roundId={roundId}
                batchId={batchId}
                ballotId={Number(ballotId)}
                ballots={ballots}
                boardName={board.name}
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
          updateAudit={updateAudit}
          boardName={board.name}
          boardId={board.id}
          jurisdictionName={audit.jurisdictions[0].name}
          jurisdictionId={audit.jurisdictions[0].id}
          electionId={electionId}
        />
      </Wrapper>
    )
  }
}

export default AuditFlow
