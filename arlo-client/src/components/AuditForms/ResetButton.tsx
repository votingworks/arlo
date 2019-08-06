import React from 'react'
import ReactDOM from 'react-dom'
import styled from 'styled-components'
import { api } from '../utilities'

const Button = styled.button`
  margin: 0 auto;
  border-radius: 5px;
  background: rgb(211, 211, 211);
  width: 155px;
  height: 30px;
  color: #000000;
  font-size: 0.4em;
  font-weight: 500;
`

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
      <Button onClick={reset}>Clear & Restart</Button>,
      resetButtonWrapper
    )
  }
  return null
}

export default ResetButton
