import React, { useState, useEffect } from 'react'
import { Spinner } from '@blueprintjs/core'
import { Route, Switch } from 'react-router-dom'
import { History } from 'history'
import {
  IAuditFlowParams,
  IAuditBoard,
  IBallot,
  IBallotInterpretation,
  IAuditBoardMember,
  IContest,
} from '../../types'
import { api } from '../utilities'
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

const loadAuditBoard = async (): Promise<IAuditBoard> => {
  return api(`/auth/me`)
}

const loadContests = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  auditBoardId: string
): Promise<IContest[]> => {
  const { contests } = await api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/audit-board/${auditBoardId}/contest`
  )
  return contests
}

const loadBallots = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  auditBoardId: string
): Promise<IBallot[]> => {
  const { ballots } = await api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/audit-board/${auditBoardId}/round/${roundId}/ballot-list`
  )
  return ballots
}

const saveMembers = async (
  electionId: string,
  jurisdictionId: string,
  auditBoardId: string,
  members: IAuditBoardMember[]
) => {
  return api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/audit-board/${auditBoardId}`,
    {
      method: 'POST',
      body: JSON.stringify({ members }),
      headers: {
        'Content-Type': 'application/json',
      },
    }
  )
}

const saveBallotInterpretations = async (
  electionId: string,
  jurisdictionId: string,
  batchId: string,
  ballotPosition: number,
  interpretations: IBallotInterpretation[]
) => {
  return api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/batch/${batchId}/ballot/${ballotPosition}`,
    {
      method: 'POST',
      body: JSON.stringify({ interpretations }),
      headers: {
        'Content-Type': 'application/json',
      },
    }
  )
}

const DataEntry: React.FC<IProps> = ({
  match: {
    params: { electionId, auditBoardId },
    url,
  },
  history,
}: IProps) => {
  const [auditBoard, setAuditBoard] = useState<IAuditBoard | null>(null)
  const [contests, setContests] = useState<IContest[] | null>(null)
  const [ballots, setBallots] = useState<IBallot[] | null>(null)

  useEffect(() => {
    ;(async () => {
      setAuditBoard(await loadAuditBoard())
    })()
  }, [electionId, auditBoardId])

  useEffect(() => {
    ;(async () => {
      if (auditBoard && auditBoard.members.length > 0) {
        const { jurisdictionId, roundId, id } = auditBoard
        setContests(await loadContests(electionId, jurisdictionId, roundId, id))
        setBallots(await loadBallots(electionId, jurisdictionId, roundId, id))
      }
    })()
  }, [electionId, auditBoard])

  const submitMembers = async (members: IAuditBoardMember[]) => {
    await saveMembers(
      electionId,
      auditBoard!.jurisdictionId,
      auditBoardId,
      members
    )
    setAuditBoard(await loadAuditBoard())
  }

  if (auditBoard && auditBoard.members.length === 0) {
    return (
      <Wrapper className="single-page">
        <MemberForm
          submitMembers={submitMembers}
          boardName={auditBoard.name}
          jurisdictionName={auditBoard.jurisdictionName}
        />
      </Wrapper>
    )
  }

  if (auditBoard && ballots && contests) {
    const nextBallot = (batchId: string, ballot: number) => () => {
      const ballotIx = ballots.findIndex(
        (b: IBallot) => b.batch.id === batchId && b.position === ballot
      )
      /* istanbul ignore else */
      if (ballotIx > -1) {
        const b = ballots[ballotIx + 1]
        history.push(`${url}/batch/${b.batch.id}/ballot/${b.position}`)
      } else {
        /* istanbul ignore next */ // covered in end to end testing
        history.push(url)
      }
    }

    const previousBallot = (batchId: string, ballot: number) => () => {
      const ballotIx = ballots.findIndex(
        (b: IBallot) => b.batch.id === batchId && b.position === ballot
      )
      /* istanbul ignore else */
      if (ballotIx > -1 && ballots[ballotIx - 1]) {
        const b = ballots[ballotIx - 1]
        history.push(`${url}/batch/${b.batch.id}/ballot/${b.position}`)
      } else {
        /* istanbul ignore next */ // covered in end to end testing
        history.push(url)
      }
    }

    const submitBallot = (batchId: string, ballotPosition: number) => async (
      interpretations: IBallotInterpretation[]
    ) => {
      const { jurisdictionId, roundId, id } = auditBoard
      await saveBallotInterpretations(
        electionId,
        jurisdictionId,
        batchId,
        ballotPosition,
        interpretations
      )
      setBallots(await loadBallots(electionId, jurisdictionId, roundId, id))
    }

    return (
      <Wrapper className="single-page">
        <Switch>
          <Route
            exact
            path="/election/:electionId/board/:auditBoardId"
            render={({ match: { url: routeURL } }) => (
              <BoardTable
                boardName={auditBoard.name}
                ballots={ballots}
                url={routeURL}
              />
            )}
          />
          <Route
            path={`${url}/batch/:batchId/ballot/:ballotPosition`}
            render={({
              match: {
                params: { batchId, ballotPosition },
              },
            }) => (
              <Ballot
                home={url}
                previousBallot={previousBallot(batchId, Number(ballotPosition))}
                nextBallot={nextBallot(batchId, Number(ballotPosition))}
                submitBallot={submitBallot(batchId, Number(ballotPosition))}
                contests={contests}
                batchId={batchId}
                ballotPosition={Number(ballotPosition)}
                ballots={ballots}
                boardName={auditBoard.name}
              />
            )}
          />
        </Switch>
      </Wrapper>
    )
  }
  return (
    <Wrapper className="single-page">
      <Spinner />
    </Wrapper>
  )
}

export default DataEntry
