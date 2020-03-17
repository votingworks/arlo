import React from 'react'
import { IAudit } from '../../../../types'
import FormButtonBar from '../../../Form/FormButtonBar'
import FormButton from '../../../Form/FormButton'

interface IProps {
  audit: IAudit
  nextStage: () => void
  prevStage: () => void
}

const Settings: React.FC<IProps> = ({ nextStage, prevStage }: IProps) => {
  return (
    <div>
      <p>Audit Settings</p>
      <FormButtonBar>
        <FormButton onClick={prevStage}>Back</FormButton>
        <FormButton onClick={nextStage}>Next</FormButton>
      </FormButtonBar>
    </div>
  )
}

export default Settings
