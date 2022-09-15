import React from 'react'
import styled from 'styled-components'
import { Tag, ProgressBar, ITagProps } from '@blueprintjs/core'

const StatusTag = styled(Tag).attrs({ minimal: true })`
  text-transform: uppercase;
  font-weight: 500;
`

const StatusTagWithProgressBar = styled(StatusTag)`
  position: relative;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;

  .bp3-progress-bar {
    position: absolute;
    bottom: -2px;
    left: 0;
    border-radius: 0;
    height: 2px;
  }
  .bp3-progress-meter {
    border-radius: 0;
  }
`

export const StatusTagWithProgress: React.FC<{
  progress: number
} & Omit<ITagProps, 'minimal'>> = ({ progress, children, ...props }) => (
  <StatusTagWithProgressBar {...props}>
    {children}
    <ProgressBar stripes={false} value={progress} intent={props.intent} />
  </StatusTagWithProgressBar>
)

export default StatusTag
