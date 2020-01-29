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
import { statusStates } from '../AuditForms/_mocks'
import { dummyBallots } from './_mocks'
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
    const audit: IAudit | IErrorResponse = await api(
      `/election/${electionId}/audit/status`
    )
    if ((audit as IErrorResponse).redirect) {
      history.push('/login')
    }
    if (checkAndToast(audit)) {
      return {
        name: '',
        riskLimit: '',
        randomSeed: '',
        contests: [],
        jurisdictions: [
          {
            auditBoards: [],
            id: '',
            name: '',
            contests: [],
          },
        ],
        rounds: [],
      }
    } else {
      return audit
    }
  }, [electionId, history])

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
      const response = await api<
        | {
            ballots: IBallot[]
          }
        | IErrorResponse
      >(
        `/election/${electionId}/jurisdiction/${audit.jurisdictions[0].id}/audit-board/${board.id}/round/${round.id}/ballot-list`
      )
      if ('redirect' in response) {
        history.push('/login')
        return []
      } else if (checkAndToast(response)) {
        return []
      } else if ('ballots' in response) {
        return response.ballots
        /* istanbul ignore next */
      } else {
        return []
      }
    } else {
      return []
    }
  }, [electionId, audit.jurisdictions, round, board, history])

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
    updateBallots()
  }, [updateBallots, audit.jurisdictions.length])

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
    const roundId = audit.rounds[Number(roundIx) - 1].id
    await api(
      `/election/${electionId}/jurisdiction/${audit.jurisdictions[0].id}/batch/${batch}/round/${roundId}/ballot/${position}`,
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
                contest={audit.contests[0].name}
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
