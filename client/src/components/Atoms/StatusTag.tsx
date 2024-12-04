import React from 'react'
import styled from 'styled-components'
import { Colors, Tag, ProgressBar, ITagProps, Intent } from '@blueprintjs/core'

// Not sure why we need to disable this rule
/* stylelint-disable value-keyword-case */
const StyledTag = styled(({ hasProgressBar: _, ...props }) => (
  <Tag {...props} minimal />
))<{
  hasProgressBar: boolean
}>`
  position: relative;
  text-transform: uppercase;
  font-weight: 500;
  ${p =>
    p.intent === 'in-progress' &&
    // Cobalt 4 in RGBA
    `background-color: rgba(69, 128, 230, 0.2);
     color: ${Colors.COBALT1}`}
  ${props =>
    props.hasProgressBar &&
    `border-bottom-left-radius: 0;
     border-bottom-right-radius: 0;`}
`

const StyledProgressBar = styled(ProgressBar).attrs({ stripes: false })`
  position: absolute;
  bottom: -2px;
  left: 0;
  border-radius: 0 0 2px 2px;
  height: 2px;

  .bp3-progress-meter {
    border-radius: 0 0 2px 2px;
  }
`

export type ExtendedIntent = Intent | 'in-progress'

export interface IStatusTagProps extends Omit<ITagProps, 'minimal' | 'intent'> {
  progress?: number
  intent?: ExtendedIntent
}

const StatusTag: React.FC<IStatusTagProps> = ({
  progress,
  children,
  ...props
}) => (
  <StyledTag {...props} hasProgressBar={progress !== undefined}>
    {children}
    {progress !== undefined && (
      <StyledProgressBar
        value={progress}
        // Filter out nonstandard Intent
        intent={
          props.intent && props.intent !== 'in-progress'
            ? props.intent
            : undefined
        }
      />
    )}
  </StyledTag>
)

export default StatusTag
