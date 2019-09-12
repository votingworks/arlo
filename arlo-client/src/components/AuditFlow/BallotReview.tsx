import React from 'react'

interface Props {
  audit: () => void
}

const BallotReview: React.FC<Props> = ({ audit }: Props) => {
  return <p>Reviewing Ballot</p>
}

export default BallotReview
