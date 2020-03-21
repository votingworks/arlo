import React from 'react'
import { IAudit } from '../../../../types'
import FormButtonBar from '../../../Form/FormButtonBar'
import FormButton from '../../../Form/FormButton'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'

interface IProps {
  audit: IAudit
  nextStage: ISidebarMenuItem
  prevStage: ISidebarMenuItem
}

const Review: React.FC<IProps> = ({ prevStage }: IProps) => {
  return (
    <div>
      <p>Review</p>
      <FormButtonBar>
        <FormButton onClick={prevStage.activate}>Back</FormButton>
      </FormButtonBar>
    </div>
  )
}

export default Review
