import React from 'react'
import { H3, H4, Colors, OL } from '@blueprintjs/core'
import styled from 'styled-components'
import { Redirect } from 'react-router-dom'
import { toast } from 'react-toastify'
import LinkButton from '../Atoms/LinkButton'
import BallotAudit from './BallotAudit'
import {
  IBallotInterpretation,
  IContest as IContestApi,
  BallotStatus,
  IContest,
  Interpretation,
} from '../../types'
import { FlushDivider } from './Atoms'
import { Inner } from '../Atoms/Wrapper'
import { useConfirm, Confirm } from '../Atoms/Confirm'
import { IBallot } from '../JurisdictionAdmin/useBallots'

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

const InstructionsList = styled(OL)`
  &.bp3-list li:not(:last-child) {
    margin-bottom: 20px;
  }
`

const ConfirmationModalTitle = styled.span`
  display: inline-block;
  margin-top: 10px;
  margin-bottom: 10px;
`

const ConfirmationModalSubTitle = styled.span`
  font-size: 16px;
  font-weight: 400;
  whitespace: normal; /* Allow long batch names to wrap */
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

  const { confirm, confirmProps } = useConfirm()

  if (!ballot) {
    return <Redirect to={home} />
  }

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
        return <h3>Blank Vote</h3>
      case Interpretation.CONTEST_NOT_ON_BALLOT:
        return <h3>Not on Ballot</h3>
      // case Interpretation.CANT_AGREE: (we do not support this case now)
      default:
        return null
    }
  }

  const confirmationModalTitle = (
    <ConfirmationModalTitle>
      Confirm the Ballot Selections
      <br />
      <ConfirmationModalSubTitle>
        Batch <b>{ballot.batch.name}</b> · Ballot Number{' '}
        <b>{ballot.position}</b>
      </ConfirmationModalSubTitle>
    </ConfirmationModalTitle>
  )

  const confirmSelections = (newInterpretations: IBallotInterpretation[]) => {
    confirm({
      title: confirmationModalTitle,
      description: (
        <>
          {contests.map((contest, i) => (
            <div key={contest.id}>
              <p>{contest.name}</p>
              {renderInterpretation(newInterpretations[i], contest)}
              <p>
                {newInterpretations[i].comment &&
                  `Comment: ${newInterpretations[i].comment}`}
              </p>
            </div>
          ))}
        </>
      ),
      onYesClick: async () => {
        await submitBallot(
          ballot.id,
          BallotStatus.AUDITED,
          newInterpretations.filter(
            ({ interpretation }) => interpretation !== null
          )
        )
        toast.success('Success! Now showing the next ballot to audit.')
        nextBallot()
      },
      yesButtonLabel: 'Confirm Selections',
      noButtonLabel: 'Change Selections',
    })
  }

  const confirmBallotNotFound = async () => {
    confirm({
      title: confirmationModalTitle,
      description: (
        <div>
          <h3>Ballot Not Found</h3>
        </div>
      ),
      onYesClick: async () => {
        await submitBallot(ballot.id, BallotStatus.NOT_FOUND, [])
        nextBallot()
      },
      yesButtonLabel: 'Confirm Selections',
      noButtonLabel: 'Change Selections',
    })
  }

  return (
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
              <BallotAudit
                ballot={ballot}
                contests={contests}
                confirmSelections={confirmSelections}
                confirmBallotNotFound={confirmBallotNotFound}
                previousBallot={previousBallot}
              />
              <Confirm {...confirmProps} />
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
