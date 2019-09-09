import React from 'react'
import { AuditFlowParams } from '../../types'

interface Props {
  match: {
    params: AuditFlowParams
  }
}

const AuditFlow: React.FC<Props> = ({
  match: {
    params: { token },
  },
}: Props) => {
  return <p>Audit: {token}</p>
}

export default AuditFlow
