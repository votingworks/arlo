import React from 'react'
import { IAudit } from '../../../../types'

interface IProps {
  audit: IAudit
  nextStage: () => void
  prevStage: () => void
}

const Settings: React.FC<IProps> = () => {
  return <p>Audit Settings</p>
}

export default Settings
