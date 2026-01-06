import React from 'react'
import styled from 'styled-components'
import { Classes, H1, H2 } from '@blueprintjs/core'
import {
  Row,
  // IFlexboxProps is needed by TS in order to export StatusBar
  // eslint-disable-next-line no-unused-vars, @typescript-eslint/no-unused-vars
  IFlexboxProps,
} from './Layout'

/**
 * A container component that shows an audit status bar. Uses space-between to
 * separate left/right children.
 */
export const StatusBar = styled(Row).attrs({
  justifyContent: 'space-between',
  className: Classes.TEXT_LARGE,
})`
  padding: 20px 0;
`

interface IAuditHeadingProps {
  auditName: string
  jurisdictionName?: string
  auditStage?: string
}

/**
 * A tag that shows the jurisdiction and audit name as well as the current stage
 * of the audit (e.g. Audit Setup, Round 1). Intended to be used as the left
 * child in StatusBar.
 */
export const AuditHeading: React.FC<IAuditHeadingProps> = ({
  auditName,
  jurisdictionName,
  auditStage,
}) => {
  return (
    <header aria-label={auditName} style={{ display: 'flex' }}>
      <H1>
        {jurisdictionName} &mdash; {auditName}
      </H1>
      {auditStage && <H2>{auditStage}</H2>}
    </header>
  )
}
