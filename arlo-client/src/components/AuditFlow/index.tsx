import React from 'react'
import styled from 'styled-components'
import { AuditFlowParams } from '../../types'

const P = styled.p`
  margin-top: 100px;
`

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
  return <P>Audit: {token}</P>
}

export default AuditFlow
