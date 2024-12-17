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
`

export const Row = styled.div`
  display: flex;
  gap: 30px;
  width: 100%;
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

export const AuditStatusTag = ({
  currentRound,
}: {
  currentRound: IRound | null
}) => {
  if (!currentRound) {
    return <StatusTag>Not Started</StatusTag>
  }
  if (currentRound.endedAt) {
    return <StatusTag intent="success">Completed</StatusTag>
  }
  return (
    <StatusTag intent="warning">
      Round {currentRound.roundNum} In Progress
    </StatusTag>
  )
}
