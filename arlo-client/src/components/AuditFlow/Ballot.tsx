import React, { useState, useEffect } from 'react'
import { H1, H3, Callout, H4, Divider, Button } from '@blueprintjs/core'
import styled from 'styled-components'
import { Redirect, Link } from 'react-router-dom'
import BallotAudit from './BallotAudit'
import BallotReview from './BallotReview'
import { IReview, IBallot } from '../../types'
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
  boardName: string
  roundIx: string
  batchId: string
  ballotId: number
  ballots: IBallot[]
  contest: string
  previousBallot: () => void
  nextBallot: () => void
  submitBallot: (
    round: string,
    batch: string,
    position: number,
    data: IReview
  ) => void
}

const Ballot: React.FC<IProps> = ({
  home,
  boardName,
  roundIx,
  batchId,
  ballotId,
  ballots,
  contest,
  previousBallot,
  nextBallot,
  submitBallot,
}: IProps) => {
  const [auditing, setAuditing] = useState(true)
  const [review, setReview] = useState<IReview>({ vote: null, comment: '' }) // eslint-disable-line no-null/no-null

  const ballotIx = ballots
    ? ballots.findIndex(
        b => b.position === ballotId && b.batch.id === batchId
      ) /* istanbul ignore next */
    : // not showing in coverage, but is tested
      -1
  const ballot = ballots[ballotIx]
  useEffect(() => {
    if (ballot) {
      const { vote, comment } = ballot
      setReview({ vote, comment: comment || '' })
    }
  }, [ballot, ballotIx])

  return !ballots || !ballot || ballotIx < 0 ? (
    <Redirect to={home} />
  ) : (
    <Wrapper>
      <TopH1>{boardName}: Ballot Card Data Entry</TopH1>
      <H3>Enter Ballot Information</H3>
      {/* eslint-disable-next-line no-null/no-null */}
      <MainCallout icon={null}>
        Round {roundIx}: auditing ballot {ballotIx + 1} of {ballots.length}
      </MainCallout>
      <BallotRow>
        <div className="ballot-side">
          <H4>Current ballot:</H4>
          <div>Tabulator: {ballot.batch.tabulator}</div>
          <div>Batch: {ballot.batch.name}</div>
          <div>Record/Position: {ballot.position}</div>
        </div>
        <Divider />
        <div className="ballot-main">
          <H4>Are you looking at the correct ballot?</H4>
          <p>
            Before continuing, check the &quot;Current ballot&quot; information
            to make sure you are entering data for the correct ballot. If the
            ballot could not be found, click &quot;Ballot not found&quot; below
            and move on to the next ballot.
          </p>
          <p>
            <Button onClick={nextBallot} intent="danger">
              Ballot {ballotId} not found - move to next ballot
            </Button>
          </p>
          <p>
            <Link to={home} className="bp3-button bp3-intent-primary">
              Return to audit overview
            </Link>
          </p>
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
          submitBallot={(data: IReview) =>
            submitBallot(roundIx, batchId, ballot.position, data)
          }
        />
      )}
    </Wrapper>
  )
}

export default Ballot
