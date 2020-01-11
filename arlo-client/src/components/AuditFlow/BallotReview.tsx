import React from 'react'
import { H3, Button } from '@blueprintjs/core'
import styled from 'styled-components'
import { IReview } from '../../types'
import { BallotRow, FormBlock, ProgressActions, FlushDivider } from './Atoms'
import FormButton from '../Form/FormButton'

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

interface IProps {
  contestName: string
  goAudit: () => void
  review: IReview
  nextBallot: () => void
  previousBallot: () => void
  submitBallot: (data: IReview) => void
}

const BallotReview: React.FC<IProps> = ({
  contestName,
  goAudit,
  review: { vote, comment },
  review,
  nextBallot,
  previousBallot,
  submitBallot,
}: IProps) => {
  const completeVote = vote as Exclude<IReview['vote'], null>
  /* eslint-disable no-console */
  const handleSubmit = async () => {
    await submitBallot(review)
    goAudit()
    nextBallot()
  }
  return (
    <BallotRow>
      <div className="ballot-side"></div>
      <div className="ballot-main">
        <FormBlock>
          <H3>{contestName}</H3>
          <FlushDivider />
          <Wrapper>
            {/* <ButtonGroup fill large vertical> */}
            <LockedButton disabled large intent="primary">
              {completeVote}
            </LockedButton>
            <Button icon="edit" minimal onClick={goAudit}>
              Edit
            </Button>
            {/* </ButtonGroup> */}
          </Wrapper>
          <p>{comment && `COMMENT: ${comment}`}</p>
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
