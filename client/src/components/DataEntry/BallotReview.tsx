import React from 'react'
import { Formik } from 'formik'
import { H3, Button } from '@blueprintjs/core'
import styled from 'styled-components'
import { IBallotInterpretation, Interpretation, IContest } from '../../types'
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
          Blank vote
        </LockedButton>
      )
    case Interpretation.CONTEST_NOT_ON_BALLOT:
      return (
        <LockedButton disabled large intent="primary">
          Not on Ballot
        </LockedButton>
      )
    case Interpretation.CANT_AGREE:
    default:
      return null
    // case for Interpretation.CANT_AGREE in case we decide to put it back in again
    // return (
    //   <LockedButton disabled large intent="primary">
    //     Audit board can&apos;t agree
    //   </LockedButton>
    // )
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
}: IProps) => (
  <Formik
    initialValues={interpretations}
    onSubmit={async () => {
      await submitBallot(interpretations)
      goAudit()
      nextBallot()
    }}
  >
    {({ isSubmitting, handleSubmit }) => (
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
            <FormButton
              loading={isSubmitting}
              type="submit"
              onClick={handleSubmit}
              intent="success"
            >
              Submit &amp; Next Ballot
            </FormButton>
            <Button onClick={goAudit} minimal>
              Back
            </Button>
          </ProgressActions>
        </div>
      </BallotRow>
    )}
  </Formik>
)

export default BallotReview
