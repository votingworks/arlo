import React from 'react'
import styled from 'styled-components'
import { Callout, H4 } from '@blueprintjs/core'
import { IStatus } from '../../types'
import FormButton from '../Form/FormButton'

const Wrapper = styled(Callout)`
  .details {
    width: 50%;
  }
  .bp3-button {
    float: right;
  }
`

interface IProps {
  status: IStatus
  electionId: string
}

const StatusBox = ({ status, electionId }: IProps) => {
  const downloadAuditReport = async (e: React.FormEvent) => {
    e.preventDefault()
    window.open(`/election/${electionId}/audit/report`)
  }

  return (
    <Wrapper>
      <H4>Status</H4>
      <div className="details">
        <p>Status</p>
      </div>
      <FormButton disabled={!status.isComplete} onClick={downloadAuditReport}>
        Download Audit Reports {!status.isComplete && '(Incomplete)'}
      </FormButton>
    </Wrapper>
  )
}

export default StatusBox
