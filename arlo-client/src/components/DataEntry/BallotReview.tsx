import React from 'react'
import { H3, Button } from '@blueprintjs/core'
import styled from 'styled-components'
import { IContest, IBallotInterpretation, Interpretation } from '../../types'
import { BallotRow, FormBlock, ProgressActions, FlushDivider } from './Atoms'
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
  { interpretation, choiceId }: IBallotInterpretation,
  contest: IContest
) => {
  switch (interpretation) {
    case Interpretation.VOTE: {
      const choice = contest.choices.find(c => c.id === choiceId)
      return choice!.name
    }
    case Interpretation.BLANK:
      return 'Blank vote/no mark'
    case Interpretation.CANT_AGREE:
      return "Audit board can't agree"
    /* istanbul ignore next */
    default:
      return ''
  }
}

interface IProps {
  contest: IContest
  goAudit: () => void
  interpretation: IBallotInterpretation
  nextBallot: () => void
  previousBallot: () => void
  submitBallot: (interpretation: IBallotInterpretation) => void
}

const BallotReview: React.FC<IProps> = ({
  contest,
  goAudit,
  interpretation,
  nextBallot,
  previousBallot,
  submitBallot,
}: IProps) => {
  const handleSubmit = async () => {
    await submitBallot(interpretation)
    goAudit()
    nextBallot()
  }

  return (
    <BallotRow>
      <div className="ballot-side"></div>
      <div className="ballot-main">
        <FormBlock>
          <H3>{contest.name}</H3>
          <FlushDivider />
          <Wrapper>
            {/* <ButtonGroup fill large vertical> */}
            <LockedButton disabled large intent="primary">
              {renderInterpretation(interpretation, contest)}
            </LockedButton>
            <Button icon="edit" minimal onClick={goAudit}>
              Edit
            </Button>
            {/* </ButtonGroup> */}
          </Wrapper>
          <p>
            {interpretation.comment && `COMMENT: ${interpretation.comment}`}
          </p>
        </FormBlock>
        <ProgressActions>
          <FormButton type="submit" onClick={handleSubmit} intent="success">
            Submit &amp; Next Ballot
          </FormButton>
          <Button onClick={previousBallot} minimal>
            Back
          </Button>
        </ProgressActions>
      </div>
    </BallotRow>
  )
}

export default BallotReview
