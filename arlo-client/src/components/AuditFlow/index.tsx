import React, { useState, useEffect, useCallback } from 'react'
import { Spinner } from '@blueprintjs/core'
import { Route, Switch } from 'react-router-dom'
import { History } from 'history'
import { toast } from 'react-toastify'
import {
  IAuditFlowParams,
  IAudit,
  IAuditBoard,
  IBallot,
  IReview,
  IErrorResponse,
} from '../../types'
import { api, poll, checkAndToast } from '../utilities'
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

  const [audit, setAudit] = useState<IAudit | undefined>(undefined) // here entereth the error monster

  const getStatus = useCallback(async (): Promise<IAudit | undefined> => {
    const audit: IAudit | IErrorResponse = await api(
      `/election/${electionId}/audit/status`
    )
    if (checkAndToast(audit)) {
      return undefined
    } else {
      return audit
    }
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

  const board: IAuditBoard | undefined = audit
    ? audit.jurisdictions[0].auditBoards.find(
        (v: IAuditBoard) => v.id === token
      )
    : undefined

  const round = audit ? audit.rounds[audit.rounds.length - 1] : undefined

  const [ballots, setBallots] = useState<IBallot[]>([])

  const getBallots = useCallback(async (): Promise<IBallot[]> => {
    /* istanbul ignore else */
    if (audit && board && round) {
      const response = await api<
        | {
            ballots: IBallot[]
          }
        | IErrorResponse
      >(
        `/election/${electionId}/jurisdiction/${audit.jurisdictions[0].id}/audit-board/${board.id}/round/${round.id}/ballot-list`
      )
      if (checkAndToast(response)) {
        return []
      } else {
        return response.ballots
      }
    } else {
      return []
    }
  }, [electionId, audit, round, board])

  const updateBallots = useCallback(async () => {
    setIsLoading(true)
    let ballots: IBallot[] = []
    poll(
      async () => {
        ballots = await getBallots()
        return !!ballots.length
      },
      () => setBallots(ballots), // tested elsewhere
      /* istanbul ignore next */ (err: Error) => toast.error(err.message)
    )
    setIsLoading(false)
  }, [getBallots])

  useEffect(() => {
    /* istanbul ignore else */
    if (audit) {
      updateBallots()
    }
  }, [updateBallots, audit])

  const nextBallot = (r: string, batchId: string, ballot: number) => () => {
    const ballotIx = ballots.findIndex(
      (b: IBallot) => b.batch.id === batchId && b.position === ballot
    )
    /* istanbul ignore else */
    if (ballotIx > -1 && ballots[ballotIx + 1]) {
      const b = ballots[ballotIx + 1]
      history.push(`${url}/round/${r}/batch/${b.batch.id}/ballot/${b.position}`)
    } else {
      /* istanbul ignore next */ // covered in end to end testing
      history.push(url)
    }
  }

  const previousBallot = (
    roundIx: string,
    batchId: string,
    ballot: number
  ) => () => {
    const ballotIx = ballots.findIndex(
      (b: IBallot) => b.batch.id === batchId && b.position === ballot
    )
    /* istanbul ignore else */
    if (ballotIx > -1 && ballots[ballotIx - 1]) {
      const b = ballots[ballotIx - 1]
      history.push(
        `${url}/round/${roundIx}/batch/${b.batch.id}/ballot/${b.position}`
      )
    } else {
      /* istanbul ignore next */ // covered in end to end testing
      history.push(url)
    }
  }

  const submitBallot = async (
    roundIx: string,
    batch: string,
    position: number,
    data: IReview
  ) => {
    /* istanbul ignore next */
    if (audit) {
      await api(
        `/election/${electionId}/jurisdiction/${audit.jurisdictions[0].id}/batch/${batch}/ballot/${position}`,
        {
          method: 'POST',
          body: JSON.stringify(data),
          headers: {
            'Content-Type': 'application/json',
          },
        }
      )
      updateBallots()
    }
  }

  /* istanbul ignore if */
  if (!audit || !board) {
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
            path={url + '/round/:roundIx/batch/:batchId/ballot/:ballotId'}
            render={({
              match: {
                params: { roundIx, batchId, ballotId },
              },
            }) => (
              <Ballot
                home={url}
                previousBallot={previousBallot(
                  roundIx,
                  batchId,
                  Number(ballotId)
                )}
                nextBallot={nextBallot(roundIx, batchId, Number(ballotId))}
                submitBallot={submitBallot}
                contest={audit.contests[0]}
                roundIx={roundIx}
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
