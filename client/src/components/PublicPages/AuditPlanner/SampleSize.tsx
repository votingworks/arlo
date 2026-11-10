import React from 'react'
import styled from 'styled-components'
import { Icon, Spinner } from '@blueprintjs/core'
import Count from '../../Atoms/Count'
import { AuditType } from '../../useAuditSettings'
import {
  BallotPollingSampleSizeKey,
  BallotPollingSampleSizeOptions,
  BallotPollingMathType,
  useProvidenceSampleSize,
  useSampleSizes,
} from './sampleSizes'
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
  ballotPollingMathType: BallotPollingMathType
  electionResults: IElectionResults
  riskLimitPercentage: number
  totalBallotsCast: number
}

const SampleSize: React.FC<IProps> = ({
  disabled,
  auditType,
  ballotPollingMathType,
  electionResults,
  riskLimitPercentage,
  totalBallotsCast,
}) => {
  const sampleSizes = useSampleSizes(electionResults)
  const isProvidence =
    auditType === 'BALLOT_POLLING' && ballotPollingMathType === 'PROVIDENCE'
  const providenceSampleSize = useProvidenceSampleSize(
    electionResults,
    riskLimitPercentage,
    isProvidence
  )
  const query = isProvidence ? providenceSampleSize : sampleSizes
  const content = (() => {
    if (disabled) {
      return <span>&mdash;</span>
    }
    if (query.isFetching) {
      return <Spinner size={CONTAINER_HEIGHT} />
    }
    if (query.error) {
      return (
        <ErrorMessage>
          <Icon icon="error" intent="danger" />
          <span>Error computing sample size</span>
        </ErrorMessage>
      )
    }

    const sampleSize = isProvidence
      ? providenceSampleSize.data?.sampleSize
      : sampleSizes.data?.[auditType][riskLimitPercentage]
    if (sampleSize === null) {
      return (
        <ErrorMessage>
          <Icon icon="info-sign" />
          <span>
            {isProvidence
              ? providenceSampleSize.data?.unsupportedReason
              : 'Not supported for uncontested contests'}
          </span>
        </ErrorMessage>
      )
    }

    // If sampleSize is empty but not null, we are still awaiting the response
    if (!sampleSize) {
      return <span>&mdash;</span>
    }

    if (auditType === 'BALLOT_POLLING') {
      const sizeOptions = sampleSize as BallotPollingSampleSizeOptions

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
            const optionSampleSize =
              sizeOptions[key as BallotPollingSampleSizeKey]
            // The server omits options it didn't compute
            if (optionSampleSize === undefined) {
              return null
            }
            return (
              <div key={key} style={{ marginBottom: '0.5rem' }}>
                {keyLabel}:{' '}
                {optionSampleSize === totalBallotsCast ? (
                  <span>Full hand tally</span>
                ) : (
                  <Count
                    count={optionSampleSize}
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

    if (sampleSize === totalBallotsCast) {
      return <span>Full hand tally</span>
    }
    if (auditType === 'BATCH_COMPARISON') {
      return (
        <Count count={sampleSize as number} singular="batch" plural="batches" />
      )
    }
    return (
      <Count count={sampleSize as number} singular="ballot" plural="ballots" />
    )
  })()
  return <Container>{content}</Container>
}

export default SampleSize
