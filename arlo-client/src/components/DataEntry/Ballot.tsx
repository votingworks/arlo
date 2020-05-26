import React, { useState, useEffect } from 'react'
import { H1, H3, Callout, H4, Button } from '@blueprintjs/core'
import styled from 'styled-components'
import { Redirect, Link } from 'react-router-dom'
import BallotAudit from './BallotAudit'
import BallotReview from './BallotReview'
import { IBallotInterpretation, IContest, BallotStatus } from '../../types'
import { BallotRow, FlushDivider } from './Atoms'

export interface IBallot {
  id: string
  batch: { id: string; name: string; tabulator: string | null }
  position: number
  status: BallotStatus
  interpretations: IBallotInterpretation[]
}

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
  batchId: string
  ballotPosition: number
  ballots: IBallot[]
  contests: IContest[]
  previousBallot: () => void
  nextBallot: () => void
  submitBallot: (
    ballotId: string,
    status: BallotStatus,
    interpretations: IBallotInterpretation[]
  ) => void
}

const emptyInterpretation = (contest: IContest) => ({
  contestId: contest.id,
  interpretation: null,
  choiceId: null,
  comment: null,
})

const Ballot: React.FC<IProps> = ({
  home,
  boardName,
  batchId,
  ballotPosition,
  ballots,
  contests,
  previousBallot,
  nextBallot,
  submitBallot,
}: IProps) => {
  const [auditing, setAuditing] = useState(true)
  const [interpretations, setInterpretations] = useState<
    IBallotInterpretation[]
  >(contests.map(emptyInterpretation))

  const ballotIx = ballots.findIndex(
    b => b.position === ballotPosition && b.batch.id === batchId
  )
  const ballot = ballots[ballotIx]

  const submitNotFound = async () => {
    await submitBallot(ballot.id, BallotStatus.NOT_FOUND, [])
    nextBallot()
  }

  useEffect(() => {
    if (ballot) {
      setInterpretations(
        contests.map(
          contest =>
            ballot.interpretations.find(i => i.contestId === contest.id) ||
            emptyInterpretation(contest)
        )
      )
    }
  }, [ballot, contests])

  return !ballot ? (
    <Redirect to={home} />
  ) : (
    <Wrapper>
      <TopH1>{boardName}: Ballot Card Data Entry</TopH1>
      <H3>Enter Ballot Information</H3>
      <MainCallout icon={null}>
        Auditing ballot {ballotIx + 1} of {ballots.length}
      </MainCallout>
      <BallotRow>
        <div className="ballot-side">
          <H4>Current ballot:</H4>
          <div>Tabulator: {ballot.batch.tabulator}</div>
          <div>Batch: {ballot.batch.name}</div>
          <div>Record/Position: {ballot.position}</div>
        </div>
        <FlushDivider />
        <div className="ballot-main">
          <H4>Are you looking at the correct ballot?</H4>
          <p>
            Before continuing, check the &quot;Current ballot&quot; information
            to make sure you are entering data for the correct ballot. If the
            ballot could not be found, click &quot;Ballot not found&quot; below
            and move on to the next ballot.
          </p>
          <p>
            <Button onClick={submitNotFound} intent="danger">
              Ballot {ballotPosition} not found - move to next ballot
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
          contests={contests}
          goReview={() => setAuditing(false)}
          interpretations={interpretations}
          setInterpretations={setInterpretations}
          previousBallot={previousBallot}
        />
      ) : (
        <BallotReview
          contests={contests}
          interpretations={interpretations}
          goAudit={() => setAuditing(true)}
          nextBallot={nextBallot}
          submitBallot={ballotInterpretations =>
            submitBallot(
              ballot.id,
              BallotStatus.AUDITED,
              ballotInterpretations.filter(
                ({ interpretation }) => interpretation !== null
              )
            )
          }
        />
      )}
    </Wrapper>
  )
}

export default Ballot
