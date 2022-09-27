import React from 'react'
import styled from 'styled-components'
import { Icon, Spinner } from '@blueprintjs/core'

import { AuditType } from '../../useAuditSettings'

const CONTAINER_HEIGHT = 36

const Container = styled.div`
  display: flex;
  font-size: 28px;
  min-height: ${CONTAINER_HEIGHT}px;
`

const Error = styled.span`
  align-items: center;
  display: flex;
  font-size: 14px;

  .bp3-icon {
    margin-right: 8px;
  }
`

interface IProps {
  auditType: Exclude<AuditType, 'HYBRID'>
  disabled?: boolean
  error?: Error
  isComputing?: boolean
  sampleSize?: number
}

const SampleSize: React.FC<IProps> = ({
  auditType,
  disabled,
  error,
  isComputing,
  sampleSize,
}) => {
  let content: JSX.Element
  if (disabled || sampleSize === undefined) {
    content = <span>&mdash;</span>
  } else if (isComputing) {
    content = <Spinner size={CONTAINER_HEIGHT} />
  } else if (error) {
    content = (
      <Error>
        <Icon icon="error" intent="danger" />
        <span>Error computing sample size</span>
      </Error>
    )
  } else if (auditType === 'BATCH_COMPARISON') {
    content = <span>{sampleSize} batches</span>
  } else {
    content = <span>{sampleSize} ballots</span>
  }
  return <Container>{content}</Container>
}

export default SampleSize
