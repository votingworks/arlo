import React, { useState } from 'react'
import { H1, H3, Callout, H4, Divider } from '@blueprintjs/core'
import styled from 'styled-components'
import BallotAudit from './BallotAudit'
import BallotReview from './BallotReview'
import { AuditBoard, Ballot } from '../../types'

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
`

const MainCallout = styled(Callout)`
  width: 400px;
  font-weight: 700;
  background-color: #202B33;
  color: #F5F8FA;
`

export const BallotRow = styled.div`
  display: flex;
  justify-content: flex-start;
  margin: 20px 0;

  .ballot-side {
    width: 200px;
    padding: 20px 0;
  }
  .ballot-main {
    width: 50%;
    padding: 20px;
  }
`

interface Props {
  roundId: string
  ballotId: string
  board: AuditBoard
}

const Ballot: React.FC<Props> = ({ roundId, ballotId, board }: Props) => {
  const [auditing, setAuditing] = useState(true)
  const [vote, setVote] = useState(null as Ballot["vote"])

  if (!board.ballots) return null // TODO handle informatively
  const ballot = board.ballots[Number(ballotId) - 1]
  if (!ballot) return null // TODO handle informatively
  setVote(ballot.vote)

  return (
    <Wrapper>
      <H1>{board.name}: Ballot Card Data Entry</H1>
      <H3>Enter Ballot Information</H3>
      <MainCallout icon={null} intent="primary">
        Round {roundId}: auditing ballot {ballotId} of {board.ballots.length}
      </MainCallout>
      <BallotRow>
        <div className="ballot-side">
          <H4>Current ballot:</H4>
          <div>Tabulator: {ballot.tabulator}</div>
          <div>Batch: {ballot.batch}</div>
          <div>Record/Position: {ballot.position}</div>
        </div>
        <Divider />
        <div className="ballot-main">
          <H4>Are you looking at the correct ballot?</H4>
          <p>
            Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do
            eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim
            ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
            aliquip ex ea commodo consequat. Duis aute irure dolor in
            reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
            pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
            culpa qui officia deserunt mollit anim id est laborum.
          </p>
        </div>
      </BallotRow>
      {auditing ? (
        <BallotAudit vote={vote} setVote={setVote} review={() => setAuditing(false)} />
      ) : (
        <BallotReview vote={vote} audit={() => setAuditing(true)} />
      )}
    </Wrapper>
  )
}

export default Ballot
