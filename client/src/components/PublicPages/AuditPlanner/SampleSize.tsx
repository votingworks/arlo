import React from 'react'
import styled from 'styled-components'
import { Icon, Spinner } from '@blueprintjs/core'
import Count from '../../Atoms/Count'
import { AuditType } from '../../useAuditSettings'
import { BallotPollingSampleSizeKey, useSampleSizes } from './sampleSizes'
import { IElectionResults } from './electionResults'

const CONTAINER_HEIGHT = 36

const Container = styled.div`
  display: flex;
  font-size: 28px;
  min-height: ${CONTAINER_HEIGHT}px;
`

const ErrorMessage = styled.span`
  align-items: center;
  display: flex;
  font-size: 14px;

  .bp3-icon {
    margin-right: 8px;
  }
`

interface IProps {
  disabled?: boolean
  auditType: Exclude<AuditType, 'HYBRID'>
  electionResults: IElectionResults
  riskLimitPercentage: string
  totalBallotsCast: number
}

const SampleSize: React.FC<IProps> = ({
  disabled,
  auditType,
  electionResults,
  riskLimitPercentage,
  totalBallotsCast,
}) => {
  const sampleSizes = useSampleSizes(electionResults)
  const content = (() => {
    if (disabled) {
      return <span>&mdash;</span>
    }
    if (sampleSizes.isFetching) {
      return <Spinner size={CONTAINER_HEIGHT} />
    }
    if (sampleSizes.error) {
      return (
        <ErrorMessage>
          <Icon icon="error" intent="danger" />
          <span>Error computing sample size</span>
        </ErrorMessage>
      )
    }

    if (!sampleSizes.data?.[auditType][riskLimitPercentage]) {
      return <span>&mdash;</span>
    }

    if (auditType === 'BALLOT_POLLING') {
      const sizeOptions = sampleSizes.data[auditType][riskLimitPercentage]

      if ('all-ballots' in sizeOptions) {
        return <span>Full hand tally</span>
      }

      const prettyKey: Record<BallotPollingSampleSizeKey, string> = {
        asn: 'ASN',
        '0.7': '70%',
        '0.8': '80%',
        '0.9': '90%',
      }
      return (
        <div>
          {Object.entries(prettyKey).map(([key, keyLabel]) => {
            const sampleSize = sizeOptions[key as BallotPollingSampleSizeKey]
            return (
              <div key={key} style={{ marginBottom: '0.5rem' }}>
                {keyLabel}:{' '}
                {sampleSize === totalBallotsCast ? (
                  <span>Full hand tally</span>
                ) : (
                  <Count
                    count={sampleSize}
                    singular="ballot"
                    plural="ballots"
                  />
                )}
              </div>
            )
          })}
        </div>
      )
    }

    const sampleSize = sampleSizes.data[auditType][riskLimitPercentage]
    if (sampleSize === totalBallotsCast) {
      return <span>Full hand tally</span>
    }
    if (auditType === 'BATCH_COMPARISON') {
      return <Count count={sampleSize} singular="batch" plural="batches" />
    }
    return <Count count={sampleSize} singular="ballot" plural="ballots" />
  })()
  return <Container>{content}</Container>
}

export default SampleSize
