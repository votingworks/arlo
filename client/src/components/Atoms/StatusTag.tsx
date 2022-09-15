import React from 'react'
import styled from 'styled-components'
import { Tag, ProgressBar, ITagProps } from '@blueprintjs/core'

const StatusTag = styled(Tag).attrs({ minimal: true })`
  text-transform: uppercase;
  font-weight: 500;
`

const StatusTagWithBar = styled.div`
  position: relative;
  .bp3-tag {
    padding-bottom: 4px;
  }
  .bp3-progress-bar {
    position: absolute;
    bottom: 0px;
    height: 2px;
    border-top-left-radius: 0;
    border-top-right-radius: 0;
  }
`

export const StatusTagWithProgress: React.FC<{
  progress: number
} & Omit<ITagProps, 'minimal'>> = ({ progress, ...props }) => (
  <StatusTagWithBar>
    <StatusTag {...props} />
    <ProgressBar stripes={false} value={progress} intent={props.intent} />
  </StatusTagWithBar>
)

export default StatusTag
