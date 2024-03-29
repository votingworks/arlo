import React, { useState, useEffect } from 'react'
import { H1 } from '@blueprintjs/core'
import { Route, Switch, useParams, useHistory } from 'react-router-dom'
import styled from 'styled-components'
import { IBallotInterpretation, IContest, BallotStatus } from '../../types'
import { api } from '../utilities'
import BoardTable from './BoardTable'
import MemberForm from './MemberForm'
import Ballot from './Ballot'
import SignOff from './SignOff'
import { Wrapper, Inner } from '../Atoms/Wrapper'
import { IAuditBoard, IMember } from '../UserContext'
import { IBallot } from '../JurisdictionAdmin/useBallots'
import { HeaderAuditBoard } from '../Header'

const PaddedInner = styled(Inner)`
  padding-top: 30px;
`

const loadAuditBoard = async (): Promise<IAuditBoard | null> => {
  const response = await api<{ user: IAuditBoard }>(`/me`)
  return response && response.user
}

const loadContests = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  auditBoardId: string
): Promise<IContest[]> => {
  const response = await api<{ contests: IContest[] }>(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/audit-board/${auditBoardId}/contest`
  )
  if (!response) {
    return []
  }
  return response.contests
}

const loadBallots = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  auditBoardId: string
): Promise<IBallot[]> => {
  const response = await api<{ ballots: IBallot[] }>(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/audit-board/${auditBoardId}/ballots`
  )
  if (!response) {
    return []
  }
  return response.ballots
}

const putMembers = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  auditBoardId: string,
  members: IMember[]
): Promise<boolean> => {
  const response = await api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/audit-board/${auditBoardId}/members`,
    {
      method: 'PUT',
      body: JSON.stringify(members),
      headers: {
        'Content-Type': 'application/json',
      },
    }
  )
  return !!response
}

const putBallotAudit = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  auditBoardId: string,
  ballotId: string,
  status: BallotStatus,
  interpretations: IBallotInterpretation[]
): Promise<boolean> => {
  const response = await api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/audit-board/${auditBoardId}/ballots/${ballotId}`,
    {
      method: 'PUT',
      body: JSON.stringify({ status, interpretations }),
      headers: {
        'Content-Type': 'application/json',
      },
    }
  )
  return !!response
}

const postSignoff = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  auditBoardId: string,
  memberNames: string[]
): Promise<boolean> => {
  const response = await api(
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
  return !!response
}

const AuditBoardView: React.FC = () => {
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
      const response = await loadAuditBoard()
      if (!response) return
      setAuditBoard(response)
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

  const submitMembers = async (members: IMember[]) => {
    const response1 = await putMembers(
      electionId,
      auditBoard!.jurisdictionId,
      auditBoard!.roundId,
      auditBoardId,
      members
    )
    if (!response1) return
    const response2 = await loadAuditBoard()
    if (!response2) return
    setAuditBoard(response2)
  }

  if (auditBoard && auditBoard.members.length === 0) {
    return (
      <Wrapper>
        <HeaderAuditBoard
          members={auditBoard.members}
          boardName={auditBoard.name}
        />
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
    const ballotIndex = ballots.findIndex(
      (b: IBallot) => b.batch.id === batchId && b.position === ballot
    )
    const nextUnauditedBallot = ballots
      .slice(ballotIndex + 1)
      .find(b => b.status === BallotStatus.NOT_AUDITED)
    if (nextUnauditedBallot) {
      history.push(
        `${url}/batch/${nextUnauditedBallot.batch.id}/ballot/${nextUnauditedBallot.position}`
      )
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
    const response1 = await putBallotAudit(
      electionId,
      jurisdictionId,
      roundId,
      auditBoardId,
      ballotId,
      status,
      interpretations
    )
    if (!response1) return
    const response2 = await loadBallots(
      electionId,
      jurisdictionId,
      roundId,
      auditBoardId
    )
    if (!response2) return
    setBallots(response2)
  }

  const submitSignoff = async (memberNames: string[]) => {
    const response1 = await postSignoff(
      electionId,
      auditBoard.jurisdictionId,
      auditBoard.roundId,
      auditBoardId,
      memberNames
    )
    if (!response1) return
    const response2 = await loadAuditBoard()
    if (!response2) return
    setAuditBoard(response2)
  }

  if (auditBoard.signedOffAt) {
    return (
      <Wrapper>
        <HeaderAuditBoard
          members={auditBoard.members}
          boardName={auditBoard.name}
        />
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
      <HeaderAuditBoard
        members={auditBoard.members}
        boardName={auditBoard.name}
      />
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
    </Wrapper>
  )
}

export default AuditBoardView
