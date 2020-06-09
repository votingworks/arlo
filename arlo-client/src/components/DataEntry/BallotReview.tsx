import React from 'react'
import { H3, Button } from '@blueprintjs/core'
import styled from 'styled-components'
import { IContest, IBallotInterpretation, Interpretation } from '../../types'
import { BallotRow, ContestCard, ProgressActions, FlushDivider } from './Atoms'
import FormButton from '../Atoms/Form/FormButton'

const Wrapper = styled.div`
  display: flex;
  justify-content: space-between;
  padding: 20px 0;
  @media (max-width: 775px) {
    flex-direction: column;
  }
`

const LockedButton = styled(FormButton)`
  text-align: center;
`

const renderInterpretation = (
  { interpretation, choiceIds }: IBallotInterpretation,
  contest: IContest
) => {
  if (!interpretation) return <div />
  switch (interpretation) {
    case Interpretation.VOTE:
      return contest.choices.map(choice =>
        choiceIds.includes(choice.id) ? (
          <LockedButton key={choice.id} disabled large intent="primary">
            {choice.name}
          </LockedButton>
        ) : null
      )
    case Interpretation.BLANK:
      return (
        <LockedButton disabled large intent="primary">
          Blank vote/Not on Ballot
        </LockedButton>
      )
    case Interpretation.CANT_AGREE:
      return (
        <LockedButton disabled large intent="primary">
          Audit board can&apos;t agree
        </LockedButton>
      )
    default:
      return null
  }
}

interface IProps {
  contests: IContest[]
  goAudit: () => void
  interpretations: IBallotInterpretation[]
  nextBallot: () => void
  submitBallot: (interpretations: IBallotInterpretation[]) => void
}

const BallotReview: React.FC<IProps> = ({
  contests,
  goAudit,
  interpretations,
  nextBallot,
  submitBallot,
}: IProps) => {
  const handleSubmit = async () => {
    await submitBallot(interpretations)
    goAudit()
    nextBallot()
  }

  return (
    <BallotRow>
      <div className="ballot-side"></div>
      <div className="ballot-main">
        {contests.map((contest, i) => (
          <ContestCard key={contest.name}>
            <H3>{contest.name}</H3>
            <FlushDivider />
            <Wrapper>
              {/* <ButtonGroup fill large vertical> */}
              {renderInterpretation(interpretations[i], contest)}
              <Button icon="edit" minimal onClick={goAudit}>
                Edit
              </Button>
              {/* </ButtonGroup> */}
            </Wrapper>
            <p>
              {interpretations[i].comment &&
                `COMMENT: ${interpretations[i].comment}`}
            </p>
          </ContestCard>
        ))}
        <ProgressActions>
          <FormButton type="submit" onClick={handleSubmit} intent="success">
            Submit &amp; Next Ballot
          </FormButton>
          <Button onClick={goAudit} minimal>
            Back
          </Button>
        </ProgressActions>
      </div>
    </BallotRow>
  )
}

export default BallotReview
