import React, { useState, useEffect } from 'react'
import { H1, H3, Callout, H4, Button } from '@blueprintjs/core'
import styled from 'styled-components'
import { Redirect, Link } from 'react-router-dom'
import BallotAudit, { IContest } from './BallotAudit'
import BallotReview from './BallotReview'
import {
  IBallotInterpretation,
  IContest as IContestApi,
  BallotStatus,
  Interpretation,
} from '../../types'
import { BallotRow, FlushDivider } from './Atoms'
import { IBallot } from '../MultiJurisdictionAudit/RoundManagement/useBallots'
import { hashBy } from '../../utils/array'

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
  contests: IContestApi[]
  previousBallot: () => void
  nextBallot: () => void
  submitBallot: (
    ballotId: string,
    status: BallotStatus,
    interpretations: IBallotInterpretation[]
  ) => void
}

const emptyInterpretation = (contest: IContest) => {
  // Special case for ballot comparison audits: if we know a contest isn't on
  // the ballot from the CVR, pre-set the interpretation to
  // CONTEST_NOT_ON_BALLOT.
  return {
    contestId: contest.id,
    interpretation: !contest.isOnBallot
      ? Interpretation.CONTEST_NOT_ON_BALLOT
      : null,
    choiceIds: [],
    comment: null,
  }
}

const Ballot: React.FC<IProps> = ({
  home,
  boardName,
  batchId,
  ballotPosition,
  ballots,
  contests: contestsFromApi,
  previousBallot,
  nextBallot,
  submitBallot,
}: IProps) => {
  const ballotIx = ballots.findIndex(
    b => b.position === ballotPosition && b.batch.id === batchId
  )
  const ballot = ballots[ballotIx]
  const contests = contestsFromApi.map(contest => ({
    ...contest,
    isOnBallot:
      ballot &&
      (!ballot.contestsOnBallot ||
        ballot.contestsOnBallot.includes(contest.id)),
  }))

  const [auditing, setAuditing] = useState(true)
  const [interpretations, setInterpretations] = useState<
    IBallotInterpretation[]
  >(contests.map(emptyInterpretation))

  const submitNotFound = async () => {
    await submitBallot(ballot.id, BallotStatus.NOT_FOUND, [])
    nextBallot()
  }

  const contestsHash = hashBy(contests, c => c.id)
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
  }, [ballot, contestsHash]) // eslint-disable-line react-hooks/exhaustive-deps

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
          {ballot.batch.container && (
            <div>Container: {ballot.batch.container}</div>
          )}
          {ballot.batch.tabulator && (
            <div>Tabulator: {ballot.batch.tabulator}</div>
          )}
          <div>Batch: {ballot.batch.name}</div>
          <div>Record/Position: {ballot.position}</div>
          {ballot.imprintedId && <div>Imprinted ID: {ballot.imprintedId}</div>}
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
