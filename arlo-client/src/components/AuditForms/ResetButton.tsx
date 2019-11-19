import React from 'react'
import ReactDOM from 'react-dom'
import { Button } from '@blueprintjs/core'
import { api } from '../utilities'

interface Props {
  updateAudit: () => void
  electionId: string
  disabled?: boolean
}

const ResetButton: React.FC<Props> = ({
  electionId,
  disabled,
  updateAudit,
}: Props) => {
  const resetButtonWrapper = document.getElementById('reset-button-wrapper')
  const reset = async () => {
    await api(`/election/${electionId}/audit/reset`, { method: 'POST' })

    updateAudit()
  }
  if (resetButtonWrapper) {
    return ReactDOM.createPortal(
      <Button onClick={reset} icon="refresh" disabled={disabled}>
        Clear &amp; Restart
      </Button>,
      resetButtonWrapper
    )
  }
  // eslint-disable-next-line no-null/no-null
  return null
}

export default ResetButton
