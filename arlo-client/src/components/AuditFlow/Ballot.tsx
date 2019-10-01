import React, { useState, useEffect } from 'react'
import { H1, H3, Callout, H4, Divider, Button } from '@blueprintjs/core'
import styled from 'styled-components'
import { Redirect } from 'react-router-dom'
import BallotAudit from './BallotAudit'
import BallotReview from './BallotReview'
import { IAuditBoard, IReview } from '../../types'
import { BallotRow } from './Atoms'

const TopH1 = styled(H1)`
  margin: 40px 0 25px 0;
`

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
`

const MainCallout = styled(Callout)`
  background-color: #137cbd;
  width: 400px;
  color: #f5f8fa;
  font-weight: 700;

  @media (max-width: 775px) {
    width: 100%;
  }
`

interface IProps {
  home: string
  roundId: string
  ballotId: string
  board: IAuditBoard
  contest: string
  previousBallot: () => void
  nextBallot: () => void
}

const Ballot: React.FC<IProps> = ({
  home,
  roundId,
  ballotId,
  board,
  contest,
  previousBallot,
  nextBallot,
}: IProps) => {
  const [auditing, setAuditing] = useState(true)
  const [review, setReview] = useState<IReview>({ vote: null, comment: '' })

  const ballot = board.ballots
    ? board.ballots.find(b => b.id === ballotId)
    : null
  useEffect(() => {
    if (ballot) {
      const { vote, comment } = ballot
      setReview({ vote, comment })
    }
  }, [ballot])

  return !board.ballots || !ballot ? (
    <Redirect to={home} />
  ) : (
    <Wrapper>
      <TopH1>{board.name}: Ballot Card Data Entry</TopH1>
      <H3>Enter Ballot Information</H3>
      <MainCallout icon={null}>
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
          <Button onClick={nextBallot} intent="danger">
            Ballot {ballotId} not found - move to next ballot
          </Button>
        </div>
      </BallotRow>
      {auditing ? (
        <BallotAudit
          contest={contest}
          review={review}
          setReview={setReview}
          previousBallot={previousBallot}
          goReview={() => setAuditing(false)}
        />
      ) : (
        <BallotReview
          contest={contest}
          review={review}
          goAudit={() => setAuditing(true)}
          nextBallot={nextBallot}
          previousBallot={() => {
            setAuditing(true)
            previousBallot()
          }}
        />
      )}
    </Wrapper>
  )
}

export default Ballot
