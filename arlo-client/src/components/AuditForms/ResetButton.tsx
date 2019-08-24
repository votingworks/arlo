import React from 'react'
import ReactDOM from 'react-dom'
import { Button } from '@blueprintjs/core'
import { api } from '../utilities'

interface Props {
  updateAudit: () => void
}

const ResetButton: React.FC<Props> = ({ updateAudit }: Props) => {
  const resetButtonWrapper = document.getElementById('reset-button-wrapper')
  const reset = async () => {
    await api(`/audit/reset`, { method: 'POST' })

    updateAudit()
  }
  if (resetButtonWrapper) {
    return ReactDOM.createPortal(
      <Button onClick={reset} icon="refresh">
        Clear &amp; Restart
      </Button>,
      resetButtonWrapper
    )
  }
  return null
}

export default ResetButton
