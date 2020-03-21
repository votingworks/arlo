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

const Settings: React.FC<IProps> = ({ nextStage, prevStage }: IProps) => {
  return (
    <div>
      <p>Audit Settings</p>
      <FormButtonBar>
        <FormButton onClick={prevStage.activate}>Back</FormButton>
        <FormButton onClick={nextStage.activate}>Next</FormButton>
      </FormButtonBar>
    </div>
  )
}

export default Settings
