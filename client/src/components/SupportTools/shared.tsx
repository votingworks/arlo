import React from 'react'

import { HTMLTable } from '@blueprintjs/core'
import styled from 'styled-components'
import StatusTag from '../Atoms/StatusTag'
import { IRound } from './support-api'

interface ColumnProps {
  isLast?: boolean
}

export const Column = styled.div<ColumnProps>`
  width: 50%;

  @media (max-width: 480px) {
    width: 100%;
  }
`

export const Row = styled.div`
  display: flex;
  gap: 30px;
  width: 100%;

  @media (max-width: 480px) {
    flex-direction: column;
  }
`

export const Table = styled(HTMLTable)`
  margin: 10px 0;
  width: 100%;
  table-layout: fixed;
  td:first-child {
    overflow: hidden;
    text-overflow: ellipsis;
  }
  td:last-child:not(:first-child) {
    padding-right: 15px;
    text-align: right;
  }
  tr td {
    vertical-align: baseline;
  }
`

// Keep the tag from being truncated next to long audit names
const auditStatusTagStyle = { flexShrink: 0 }

export const AuditStatusTag = ({
  currentRound,
}: {
  currentRound: IRound | null
}): JSX.Element => {
  if (!currentRound) {
    return <StatusTag style={auditStatusTagStyle}>Not Started</StatusTag>
  }
  if (currentRound.endedWithFullTallyEscalation) {
    return (
      <StatusTag intent="danger" style={auditStatusTagStyle}>
        Blocked
      </StatusTag>
    )
  }
  if (currentRound.endedAt) {
    return (
      <StatusTag intent="success" style={auditStatusTagStyle}>
        Completed
      </StatusTag>
    )
  }
  return (
    <StatusTag intent="warning" style={auditStatusTagStyle}>
      Round {currentRound.roundNum} In Progress
    </StatusTag>
  )
}
