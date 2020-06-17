import React, { useState, useEffect } from 'react'
import { H1 } from '@blueprintjs/core'
import { Route, Switch, useParams, useHistory } from 'react-router-dom'
import styled from 'styled-components'
import { toast } from 'react-toastify'
import {
  IAuditBoard,
  IBallotInterpretation,
  IAuditBoardMember,
  IContest,
  BallotStatus,
} from '../../types'
import { api } from '../utilities'
import BoardTable from './BoardTable'
import MemberForm from './MemberForm'
import Ballot, { IBallot } from './Ballot'
import SignOff from './SignOff'
import { Wrapper, Inner } from '../Atoms/Wrapper'

const PaddedInner = styled(Inner)`
  padding-top: 30px;
`

const loadAuditBoard = async (): Promise<IAuditBoard> => {
  return api(`/me`)
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
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/audit-board/${auditBoardId}/ballots`
  )
  return ballots
}

const putMembers = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  auditBoardId: string,
  members: IAuditBoardMember[]
) => {
  try {
    await api(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/audit-board/${auditBoardId}/members`,
      {
        method: 'PUT',
        body: JSON.stringify(members),
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )
  } catch (err) {
    toast.error(err.message)
  }
}

const putBallotAudit = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  auditBoardId: string,
  ballotId: string,
  status: BallotStatus,
  interpretations: IBallotInterpretation[]
) => {
  try {
    await api(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/audit-board/${auditBoardId}/ballots/${ballotId}`,
      {
        method: 'PUT',
        body: JSON.stringify({ status, interpretations }),
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )
  } catch (err) {
    toast.error(err.message)
  }
}

const postSignoff = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  auditBoardId: string,
  memberNames: string[]
) => {
  try {
    await api(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/audit-board/${auditBoardId}/sign-off`,
      {
        method: 'POST',
        body: JSON.stringify({
          memberName1: memberNames[0] || '',
          memberName2: memberNames[1] || '',
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )
  } catch (err) {
    toast.error(err.message)
  }
}

const DataEntry: React.FC = () => {
  const history = useHistory()
  const { electionId, auditBoardId } = useParams<{
    electionId: string
    auditBoardId: string
  }>()
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
    await putMembers(
      electionId,
      auditBoard!.jurisdictionId,
      auditBoard!.roundId,
      auditBoardId,
      members
    )
    setAuditBoard(await loadAuditBoard())
  }

  if (auditBoard && auditBoard.members.length === 0) {
    return (
      <Wrapper>
        <PaddedInner>
          <MemberForm
            submitMembers={submitMembers}
            boardName={auditBoard.name}
            jurisdictionName={auditBoard.jurisdictionName}
          />
        </PaddedInner>
      </Wrapper>
    )
  }

  if (!auditBoard || !ballots || !contests) return null // Still loading

  const url = `/election/${electionId}/audit-board/${auditBoardId}`

  const nextBallot = (batchId: string, ballot: number) => () => {
    const ballotIx = ballots.findIndex(
      (b: IBallot) => b.batch.id === batchId && b.position === ballot
    )
    /* istanbul ignore else */
    if (ballotIx > -1 && ballots[ballotIx + 1]) {
      const b = ballots[ballotIx + 1]
      history.push(`${url}/batch/${b.batch.id}/ballot/${b.position}`)
    } else {
      /* istanbul ignore next */ // covered in end to end testing
      history.push(url)
    }
    window.scrollTo(0, 0)
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
    window.scrollTo(0, 0)
  }

  const submitBallot = async (
    ballotId: string,
    status: BallotStatus,
    interpretations: IBallotInterpretation[]
  ) => {
    const { jurisdictionId, roundId } = auditBoard
    await putBallotAudit(
      electionId,
      jurisdictionId,
      roundId,
      auditBoardId,
      ballotId,
      status,
      interpretations
    )
    setBallots(
      await loadBallots(electionId, jurisdictionId, roundId, auditBoardId)
    )
  }

  const submitSignoff = async (memberNames: string[]) => {
    await postSignoff(
      electionId,
      auditBoard.jurisdictionId,
      auditBoard.roundId,
      auditBoardId,
      memberNames
    )
    setAuditBoard(await loadAuditBoard())
  }

  if (auditBoard.signedOffAt) {
    return (
      <Wrapper>
        <PaddedInner>
          <div>
            <H1>{auditBoard.name}: Auditing Complete</H1>
            <p>Your work here is done!</p>
          </div>
        </PaddedInner>
      </Wrapper>
    )
  }

  return (
    <Wrapper>
      <PaddedInner>
        <Switch>
          <Route
            exact
            path="/election/:electionId/audit-board/:auditBoardId"
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
                submitBallot={submitBallot}
                contests={contests}
                batchId={batchId}
                ballotPosition={Number(ballotPosition)}
                ballots={ballots}
                boardName={auditBoard.name}
              />
            )}
          />
          <Route
            path={`${url}/signoff`}
            render={() => (
              <SignOff auditBoard={auditBoard} submitSignoff={submitSignoff} />
            )}
          />
        </Switch>
      </PaddedInner>
    </Wrapper>
  )
}

export default DataEntry
