import React from 'react'

interface Props {
  review: () => void
}

const BallotAudit: React.FC<Props> = ({ review }: Props) => {
  return <p>Auditing Ballot</p>
}

export default BallotAudit
