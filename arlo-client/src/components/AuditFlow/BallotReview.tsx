import React from 'react'
import { H3, Divider, Button } from '@blueprintjs/core'
import styled from 'styled-components'
import { IReview } from '../../types'
import { BallotRow, FormBlock, ProgressActions } from './Atoms'
import FormButton from '../Form/FormButton'
import BlockRadio from './BlockRadio'

const Wrapper = styled.div`
  display: flex;
  justify-content: space-between;
  padding: 20px 0;
`

const SingleBlockRadio = styled(BlockRadio)`
  &.bp3-control.bp3-radio {
    margin: 0;
  }
`

interface IProps {
  contest: string
  goAudit: () => void
  review: IReview
  nextBallot: () => void
}

const BallotReview: React.FC<IProps> = ({
  contest,
  goAudit,
  review: { vote, comment },
  nextBallot,
}: IProps) => {
  const completeVote = vote as Exclude<IReview['vote'], null>
  /* eslint-disable no-console */
  const handleSubmit = () => {
    console.log(completeVote, comment)
    goAudit()
    nextBallot()
  }
  return (
    <BallotRow>
      <div className="ballot-side"></div>
      <div className="ballot-main">
        <FormBlock>
          <H3>{contest}</H3>
          <Divider />
          <Wrapper>
            <SingleBlockRadio value={completeVote} locked />
            <Button onClick={goAudit} icon="edit" minimal>
              Edit
            </Button>
          </Wrapper>
          <p>COMMENT: {comment}</p>
        </FormBlock>
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
