import React, { useState, useEffect } from 'react'
import { H3, H4, H5, Button, Colors, OL } from '@blueprintjs/core'
import styled from 'styled-components'
import { Redirect } from 'react-router-dom'
import LinkButton from '../Atoms/LinkButton'
import BallotAudit from './BallotAudit'
import BallotReview from './BallotReview'
import {
  IBallotInterpretation,
  IContest as IContestApi,
  BallotStatus,
  IContest,
} from '../../types'
import { FlushDivider } from './Atoms'
import { Inner } from '../Atoms/Wrapper'
import { IBallot } from '../MultiJurisdictionAudit/RoundManagement/useBallots'
import { hashBy } from '../../utils/array'

const TopH3 = styled(H3)`
  display: inline-block;
  margin-bottom: 0;
  margin-left: 20px;
  font-weight: 500;
`

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
`

const ContentWrapper = styled.div`
  display: flex;
  margin-top: 30px;
  width: 100%;
  @media only screen and (max-width: 767px) {
    flex-direction: column;
  }
`

const BallotWrapper = styled.div`
  width: 70%;
  @media only screen and (max-width: 767px) {
    order: 2;
    width: 100%;
  }
`

const InstructionsWrapper = styled.div`
  width: 30%;
  padding-left: 30px;
  @media only screen and (max-width: 767px) {
    order: 1;
    width: 100%;
    padding-left: 0;
  }
`

const BallotMainRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
`

const SubTitle = styled(H5)`
  margin-bottom: 0;
  color: ${Colors.BLACK};
  font-weight: 400;
`

const BallotRowValue = styled(H4)`
  margin-bottom: 0;
  color: ${Colors.BLACK};
`

const SmallButton = styled(LinkButton)`
  border: 1px solid ${Colors.GRAY4};
  border-radius: 5px;
`

const TopRow = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 20px;
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

const emptyInterpretation = (contest: IContest) => ({
  contestId: contest.id,
  interpretation: null,
  choiceIds: [],
  comment: null,
})

const Ballot: React.FC<IProps> = ({
  home,
  batchId,
  ballotPosition,
  ballots,
  contests,
  previousBallot,
  nextBallot,
  submitBallot,
}: IProps) => {
  const ballotIx = ballots.findIndex(
    b => b.position === ballotPosition && b.batch.id === batchId
  )
  const ballot = ballots[ballotIx]

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
    <Inner>
      <Wrapper>
        <ContentWrapper>
          <BallotWrapper>
            <TopRow>
              <SmallButton to={home} minimal icon="caret-left">
                All Ballots
              </SmallButton>
              <TopH3>Audit Board Selections</TopH3>
            </TopRow>
            <FlushDivider />
            <BallotMainRow>
              <div>
                <SubTitle>batch</SubTitle>
                <BallotRowValue>{ballot.batch.name}</BallotRowValue>
              </div>
              <div>
                <SubTitle>position</SubTitle>
                <BallotRowValue>{ballot.position}</BallotRowValue>
              </div>
              {ballot.batch.container && (
                <div>
                  <SubTitle>container</SubTitle>
                  <BallotRowValue>{ballot.batch.container}</BallotRowValue>
                </div>
              )}
              {ballot.batch.tabulator && (
                <div>
                  <SubTitle>tabulator</SubTitle>
                  <BallotRowValue>{ballot.batch.tabulator}</BallotRowValue>
                </div>
              )}
              {ballot.imprintedId !== undefined && (
                <div>
                  <SubTitle>imprint</SubTitle>
                  <BallotRowValue>{ballot.imprintedId}</BallotRowValue>
                </div>
              )}
              <div>
                <Button onClick={submitNotFound} intent="danger">
                  Ballot Not Found
                </Button>
              </div>
            </BallotMainRow>
            <FlushDivider />
            <div>
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
            </div>
          </BallotWrapper>
          <InstructionsWrapper>
            <H4>Instructions</H4>
            <OL>
              <li>
                Confirm that you are looking at the correct ballot for the batch
                and position. If the ballot was not located, select{' '}
                <strong>Ballot Not Found at the top of the screen.</strong>
              </li>
              <li>
                For each contest, select all the candidate/choices which you see
                marked on the paper ballot. Select <strong>Blank Vote</strong>{' '}
                if the voter did not make any selections. Select{' '}
                <strong>Not on Ballot</strong> if the contest does not appear on
                the ballot.
              </li>
              <li>
                Once all votes are recorded, <strong>Submit Selections</strong>{' '}
                and proceed to the next ballot until all ballots have been
                audited.
              </li>
            </OL>
          </InstructionsWrapper>
        </ContentWrapper>
      </Wrapper>
    </Inner>
  )
}

export default Ballot
