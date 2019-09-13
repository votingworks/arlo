import React from 'react'
import { Ballot } from '../../types';

interface Props {
  audit: () => void
  vote: Ballot["vote"]
}

const BallotReview: React.FC<Props> = ({ audit }: Props) => {
  return <p>Reviewing Ballot</p>
}

export default BallotReview
