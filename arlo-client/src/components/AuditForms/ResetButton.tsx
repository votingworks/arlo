import React from 'react'
import ReactDOM from 'react-dom'
import { Button } from '@blueprintjs/core'
import { api } from '../utilities'

interface OwnProps {
  updateAudit: () => void
}

const ResetButton = (props: OwnProps) => {
  const resetButtonWrapper = document.getElementById('reset-button-wrapper')
  const reset = async () => {
    await api(`/audit/reset`, { method: 'POST' })

    props.updateAudit()
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
