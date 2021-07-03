import React, { useState, useEffect, useRef } from 'react'
import { H3, H4, Button, Colors, OL } from '@blueprintjs/core'
import styled from 'styled-components'
import { Redirect } from 'react-router-dom'
import LinkButton from '../Atoms/LinkButton'
import BallotAudit from './BallotAudit'
import {
  IBallotInterpretation,
  IContest as IContestApi,
  BallotStatus,
  IContest,
  Interpretation,
} from '../../types'
import { FlushDivider, SubTitle } from './Atoms'
import { Inner } from '../Atoms/Wrapper'
import { IBallot } from '../MultiJurisdictionAudit/RoundManagement/useBallots'
import { hashBy } from '../../utils/array'
import { useConfirm, Confirm } from '../Atoms/Confirm'

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
  width: 75%;
  @media only screen and (max-width: 767px) {
    order: 2;
    width: 100%;
  }
`

const InstructionsWrapper = styled.div`
  width: 25%;
  padding-left: 30px;
  @media only screen and (max-width: 767px) {
    order: 1;
    width: 100%;
    padding-left: 0;
  }
`

const BallotMainRow = styled.div`
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
`

const BallotRowValue = styled(H4)`
  margin-bottom: 0;
  color: ${Colors.BLACK};
`

const SmallButton = styled(LinkButton)`
  border: 1px solid ${Colors.GRAY4};
  border-radius: 5px;
  color: ${Colors.BLACK};
  font-size: 16px;
`

const TopRow = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 20px;
`

const NotFoundButton = styled(Button)`
  border-radius: 5px;
  width: 13.5em;
  font-weight: 600;
  &.bp3-button.bp3-large {
    height: 2em;
    min-height: auto;
    font-size: 14px;
  }
  @media only screen and (max-width: 767px) {
    width: auto;
  }
`

const InstructionsList = styled(OL)`
  &.bp3-list li:not(:last-child) {
    margin-bottom: 20px;
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

  const [interpretations, setInterpretations] = useState<
    IBallotInterpretation[]
  >(contests.map(emptyInterpretation))
  const { confirm, confirmProps } = useConfirm()

  const interpretiationsRef = useRef<IBallotInterpretation[]>(
    contests.map(emptyInterpretation)
  )
  interpretiationsRef.current = interpretations

  const renderInterpretation = (
    { interpretation, choiceIds }: IBallotInterpretation,
    contest: IContest
  ) => {
    if (!interpretation) return <div />
    switch (interpretation) {
      case Interpretation.VOTE:
        return contest.choices.map(choice =>
          choiceIds.includes(choice.id) ? (
            <h3 key={choice.id}>{choice.name}</h3>
          ) : null
        )
      case Interpretation.BLANK:
        return <h3>Blank vote</h3>
      case Interpretation.CONTEST_NOT_ON_BALLOT:
        return <h3>Not on Ballot</h3>
      // case Interpretation.CANT_AGREE:
      // case for Interpretation.CANT_AGREE in case we decide to put it back in again
      // return (
      //   <LockedButton disabled large intent="primary">
      //     Audit board can&apos;t agree
      //   </LockedButton>
      // )
      default:
        return null
    }
  }

  const ballotSubmitFunc = (isNotFound: boolean) =>
    isNotFound
      ? submitBallot(ballot.id, BallotStatus.NOT_FOUND, [])
      : submitBallot(
          ballot.id,
          BallotStatus.AUDITED,
          interpretiationsRef.current.filter(
            ({ interpretation }) => interpretation !== null
          )
        )

  const initiateConfirm = (isNotFound: boolean) =>
    confirm({
      title: 'Confirm the Ballot Selections',
      description: (
        <>
          {contests.map((contest, i) => (
            <div key={contest.id}>
              <p>{contest.name}</p>
              {isNotFound ? (
                <h3>Ballot Not Found</h3>
              ) : (
                <>
                  {renderInterpretation(
                    interpretiationsRef.current[i],
                    contest
                  )}
                  <p>
                    {interpretiationsRef.current[i].comment &&
                      `Comment: ${interpretiationsRef.current[i].comment}`}
                  </p>
                </>
              )}
            </div>
          ))}
        </>
      ),
      onYesClick: async () => {
        ballotSubmitFunc(isNotFound)
        nextBallot()
      },
      yesButtonLabel: 'Confirm Selections',
      noButtonLabel: 'Change Selections',
    })

  const setInterpretationsFunc = (
    newInterpretations: IBallotInterpretation[]
  ) => {
    setInterpretations(newInterpretations)
    initiateConfirm(true)
  }

  const submitNotFound = async () => {
    initiateConfirm(true)
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
    <div>
      <Inner>
        <Wrapper>
          <ContentWrapper>
            <BallotWrapper>
              <TopRow>
                <SmallButton to={home} minimal icon="caret-left">
                  All Ballots
                </SmallButton>
                <TopH3>Audit Ballot Selections</TopH3>
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
                  <NotFoundButton
                    onClick={submitNotFound}
                    intent="danger"
                    large
                  >
                    Ballot Not Found
                  </NotFoundButton>
                </div>
              </BallotMainRow>
              <FlushDivider />
              <div>
                <BallotAudit
                  contests={contests}
                  interpretations={interpretations}
                  setInterpretations={setInterpretationsFunc}
                  previousBallot={previousBallot}
                />
                <Confirm {...confirmProps} />
              </div>
            </BallotWrapper>
            <InstructionsWrapper>
              <H4>Instructions</H4>
              <InstructionsList>
                <li>
                  Confirm that you are looking at the correct ballot for the
                  batch and position. If the ballot was not located, select{' '}
                  <strong>Ballot Not Found</strong> at the top of the screen.
                </li>
                <li>
                  For each contest, select all the candidate/choices which you
                  see marked on the paper ballot. Select{' '}
                  <strong>Blank Vote</strong> if the voter did not make any
                  selections. Select <strong>Not on Ballot</strong> if the
                  contest does not appear on the ballot.
                </li>
                <li>
                  Once all votes are recorded,{' '}
                  <strong>Submit Selections</strong> and proceed to the next
                  ballot until all ballots have been audited.
                </li>
              </InstructionsList>
            </InstructionsWrapper>
          </ContentWrapper>
        </Wrapper>
      </Inner>
    </div>
  )
}

export default Ballot
