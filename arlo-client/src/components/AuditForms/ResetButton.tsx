import React from 'react'
import ReactDOM from 'react-dom'
import { Button } from '@blueprintjs/core'
import { toast } from 'react-toastify'
import { api, checkAndToast } from '../utilities'
import { IErrorResponse } from '../../types'

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
  const resetButtonWrapper = document.getElementById('reset-button-wrapper')
  const reset = async () => {
    try {
      const response: IErrorResponse = await api(
        `/election/${electionId}/audit/reset`,
        { method: 'POST' }
      )
      if (checkAndToast(response)) {
        return
      }
      updateAudit()
    } catch (err) {
      toast.error(err.message)
    }
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
