import React from 'react'
import { IAudit } from '../../../../types'

interface IProps {
  audit: IAudit
  nextStage: () => void
  prevStage: () => void
}

const Review: React.FC<IProps> = () => {
  return <p>Review &amp; Launch</p>
}

export default Review
