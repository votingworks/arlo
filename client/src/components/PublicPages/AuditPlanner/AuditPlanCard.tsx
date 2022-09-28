import React, { useEffect, useRef, useState } from 'react'
import styled from 'styled-components'
import { Card, H2, H3, Slider } from '@blueprintjs/core'

import SampleSize from './SampleSize'
import SegmentedControl from '../../Atoms/SegmentedControl'
import { AuditType } from '../../useAuditSettings'
import { IElectionResults } from './electionResults'
import { useSampleSizes } from './sampleSizes'

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

const DEFAULT_RISK_LIMIT_PERCENTAGE = 5

interface IProps {
  disabled: boolean
  electionResults: IElectionResults
}

const AuditPlanCard: React.FC<IProps> = ({ disabled, electionResults }) => {
  // Scroll the card, specifically the sample size, into view when it first appears
  const sampleSizeSectionRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (sampleSizeSectionRef.current) {
      sampleSizeSectionRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [])

  const [selectedAuditType, setSelectedAuditType] = useState<
    Exclude<AuditType, 'HYBRID'>
  >('BALLOT_POLLING')
  const [riskLimitPercentage, setRiskLimitPercentage] = useState(
    DEFAULT_RISK_LIMIT_PERCENTAGE
  )
  const [
    debouncedRiskLimitPercentage,
    setDebouncedRiskLimitPercentage,
  ] = useState(riskLimitPercentage)
  const sampleSizes = useSampleSizes(electionResults, {
    // We display an inline error message instead
    showToastOnError: false,
  })

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
              { label: 'Ballot Polling', value: 'BALLOT_POLLING' },
              { label: 'Ballot Comparison', value: 'BALLOT_COMPARISON' },
              { label: 'Batch Comparison', value: 'BATCH_COMPARISON' },
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
            onRelease={setDebouncedRiskLimitPercentage}
            value={riskLimitPercentage}
          />
        </Section>
      </InnerContainer>

      <SampleSizeSection ref={sampleSizeSectionRef}>
        <SubHeading>Estimated Sample Size</SubHeading>
        <SampleSize
          auditType={selectedAuditType}
          disabled={disabled}
          error={sampleSizes.error || undefined}
          isComputing={sampleSizes.isFetching}
          sampleSize={
            sampleSizes.data?.[selectedAuditType][
              debouncedRiskLimitPercentage.toString()
            ]
          }
        />
      </SampleSizeSection>
    </Container>
  )
}

export default AuditPlanCard
