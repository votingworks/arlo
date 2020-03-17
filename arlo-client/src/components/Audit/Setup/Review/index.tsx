import React from 'react'
import { IAudit } from '../../../../types'
import FormButtonBar from '../../../Form/FormButtonBar'
import FormButton from '../../../Form/FormButton'

interface IProps {
  audit: IAudit
  nextStage: () => void
  prevStage: () => void
}

const Review: React.FC<IProps> = ({ prevStage }: IProps) => {
  return (
    <div>
      <p>Review</p>
      <FormButtonBar>
        <FormButton onClick={prevStage}>Back</FormButton>
      </FormButtonBar>
    </div>
  )
}

export default Review
