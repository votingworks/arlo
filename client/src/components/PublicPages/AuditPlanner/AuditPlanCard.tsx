import React, { useEffect, useState } from 'react'
import styled from 'styled-components'
import { Card, H2, H3, Icon, Slider, Spinner } from '@blueprintjs/core'

import SegmentedControl from '../../Atoms/SegmentedControl'
import { AuditType, useSampleSizes } from './sampleSizes'
import { IElectionResults } from './electionResults'
import { useDebounce } from '../../../utils/debounce'

interface IContainerProps {
  disabled?: boolean
}

const Container = styled(Card)<IContainerProps>`
  &.bp3-card {
    margin: auto;
    margin-top: 24px;
    margin-bottom: 72px;
    opacity: ${props => (props.disabled ? '0.5' : '1')}
    padding: 0;
    width: 640px;
  }
`

const InnerContainer = styled.div`
  padding: 32px;
`

const Heading = styled(H2)`
  &.bp3-heading {
    margin-bottom: 32px;
  }
`

const Section = styled.div`
  margin-bottom: 32px;

  &:last-child {
    margin-bottom: 0;
  }
`

const SubHeading = styled(H3)`
  &.bp3-heading {
    font-size: 14px;
    margin-bottom: 8px;
  }
`

const SampleSizeSection = styled.div`
  background: #f3f8ff; // A custom tint of Blueprint v4 @blue5
  border-bottom-left-radius: 3px; // Match Blueprint card
  border-bottom-right-radius: 3px; // Match Blueprint card
  padding: 32px;
`

const SAMPLE_SIZE_CONTAINER_HEIGHT = 36

const SampleSize = styled.div`
  display: flex;
  font-size: 28px;
  min-height: ${SAMPLE_SIZE_CONTAINER_HEIGHT}px;
`

const SampleSizeError = styled.span`
  align-items: center;
  display: flex;
  font-size: 14px;

  .bp3-icon {
    margin-right: 8px;
  }
`

const DEFAULT_RISK_LIMIT_PERCENTAGE = 5

interface IProps {
  disabled: boolean
  electionResults: IElectionResults
}

const AuditPlanCard: React.FC<IProps> = ({ disabled, electionResults }) => {
  // Scroll to the bottom of the screen when the audit plan card first appears
  useEffect(() => {
    window.scrollTo(0, document.body.scrollHeight)
  }, [])

  const [selectedAuditType, setSelectedAuditType] = useState<AuditType>(
    'ballotPolling'
  )
  const [riskLimitPercentage, setRiskLimitPercentage] = useState(
    DEFAULT_RISK_LIMIT_PERCENTAGE
  )
  const [
    debouncedRiskLimitPercentage,
    isDebouncingRiskLimitPercentage,
  ] = useDebounce(riskLimitPercentage, 500)
  const sampleSizes = useSampleSizes(
    electionResults,
    debouncedRiskLimitPercentage,
    {
      minFetchDurationMs: isDebouncingRiskLimitPercentage ? 500 : 1000,
      showToastOnError: false, // We display an inline error message instead
    }
  )

  const isComputingSampleSizes =
    isDebouncingRiskLimitPercentage || sampleSizes.isFetching

  return (
    <Container data-testid="auditPlanCard" disabled={disabled} elevation={1}>
      <InnerContainer>
        <Heading>Audit Plan</Heading>

        <Section>
          <SubHeading id="auditMethodLabel">Audit Method</SubHeading>
          <SegmentedControl
            aria-labelledby="auditMethodLabel"
            disabled={disabled}
            fill
            large
            onChange={setSelectedAuditType}
            options={[
              { label: 'Ballot Polling', value: 'ballotPolling' },
              { label: 'Ballot Comparison', value: 'ballotComparison' },
              { label: 'Batch Comparison', value: 'batchComparison' },
            ]}
            value={selectedAuditType}
          />
        </Section>

        <Section>
          <SubHeading>Risk Limit</SubHeading>
          <Slider
            disabled={disabled}
            labelRenderer={value => (
              <span
                // A hack to display the listed values on both the slider axis and the slider label,
                // and all other values on only the slider label. More recent versions of the
                // Blueprint slider actually support this differentiation
                style={{
                  color: [0, 5, 10, 15, 20].includes(value)
                    ? undefined
                    : 'white',
                }}
              >
                {value}%
              </span>
            )}
            min={0}
            max={20}
            onChange={setRiskLimitPercentage}
            value={riskLimitPercentage}
          />
        </Section>
      </InnerContainer>

      <SampleSizeSection>
        <SubHeading>Estimated Sample Size</SubHeading>
        <SampleSize>
          {isComputingSampleSizes ? (
            <Spinner size={SAMPLE_SIZE_CONTAINER_HEIGHT} />
          ) : disabled ? (
            <span>&mdash;</span>
          ) : sampleSizes.isError ? (
            <SampleSizeError>
              <Icon icon="error" intent="danger" />
              <span>Error computing sample size</span>
            </SampleSizeError>
          ) : (
            <span>{sampleSizes?.data?.[selectedAuditType]} ballots</span>
          )}
        </SampleSize>
      </SampleSizeSection>
    </Container>
  )
}

export default AuditPlanCard
