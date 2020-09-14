import React from 'react'
import ReactDOM from 'react-dom'
import { Button } from '@blueprintjs/core'
import { api } from './utilities'
import { IErrorResponse } from '../types'
import { useAuthDataContext } from './UserContext'

interface IProps {
  updateAudit: () => void
  electionId: string
  disabled?: boolean
}

const ResetButton: React.FC<IProps> = ({
  electionId,
  disabled,
  updateAudit,
}: IProps) => {
  const { isAuthenticated } = useAuthDataContext()
  const resetButtonWrapper = document.getElementById('reset-button-wrapper')
  const reset = async () => {
    const response = await api<IErrorResponse>(
      `/election/${electionId}/audit/reset`,
      { method: 'POST' }
    )
    if (!response) {
      return
    }
    updateAudit()
  }
  if (resetButtonWrapper && !isAuthenticated) {
    return ReactDOM.createPortal(
      <Button onClick={reset} icon="refresh" disabled={disabled}>
        Clear &amp; Restart
      </Button>,
      resetButtonWrapper
    )
  }
  return null
}

export default ResetButton
