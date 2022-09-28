import React from 'react'
import styled from 'styled-components'
import { Icon, Spinner } from '@blueprintjs/core'

import Count from '../../Atoms/Count'
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
  if (disabled) {
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
  } else if (sampleSize === undefined) {
    content = <span>&mdash;</span>
  } else if (auditType === 'BATCH_COMPARISON') {
    content = <Count count={sampleSize} plural="batches" singular="batch" />
  } else {
    content = <Count count={sampleSize} plural="ballots" singular="ballot" />
  }
  return <Container>{content}</Container>
}

export default SampleSize
