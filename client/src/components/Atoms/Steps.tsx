import React from 'react'
import styled from 'styled-components'
import { Card, Colors, Icon } from '@blueprintjs/core'

/**
 * A set of components to display a multi-step process. Consists of a card
 * containing:
 *  - a step progress list (top)
 *  - a step content panel (middle)
 *  - a step actions bar (bottom)
 *
 * These components are purely graphical - the parent must manage all state
 * (current step, disabling, etc.)
 *
 * Example usage:
 *
 *  <Steps>
 *    <StepProgress steps=["Log In", "Prepare", "Audit"] currentStep="Prepare" />
 *    <StepPanel>Prepare your ballots</StepPanel>
 *    <StepActions
 *      left={<Button>Back</Button>}
 *      right={<Button>Next</Button>}
 *    />
 *  </Steps>
 */

export const Steps = styled(Card).attrs({ elevation: 1 })`
  padding: 0;
`

const StepProgressRow = styled.ol`
  background-color: ${Colors.LIGHT_GRAY5};
  display: flex;
  align-items: center;
  padding: 25px;
  margin: 0;
  border-radius: 3px 3px 0 0;
`

const StepProgressStep = styled.li`
  display: flex;
  align-items: center;
`

const StepProgressCircle = styled.div<{ incomplete: boolean }>`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 30px;
  width: 30px;
  border-radius: 50%;
  background-color: ${props =>
    props.incomplete ? Colors.GRAY4 : Colors.BLUE3};
  margin-right: 10px;
  color: ${Colors.WHITE};
  font-weight: 500;
`

const StepProgressLabel = styled.div<{ incomplete: boolean }>`
  color: ${props => (props.incomplete ? Colors.GRAY3 : 'inherit')};
  font-weight: 700;
`

const StepProgressLine = styled.div`
  flex-grow: 1;
  height: 1px;
  background: ${Colors.GRAY5};
  margin: 0 10px;
`

export const StepProgress: React.FC<{
  steps: readonly string[]
  currentStep: string
}> = ({ steps, currentStep }) => {
  const currentStepIndex = steps.indexOf(currentStep)
  return (
    <StepProgressRow>
      {steps.map((step, i) => (
        <React.Fragment key={step}>
          <StepProgressStep
            aria-label={step}
            aria-current={i === currentStepIndex ? 'step' : undefined}
          >
            <StepProgressCircle incomplete={i > currentStepIndex}>
              {i < currentStepIndex ? <Icon icon="tick" /> : i + 1}
            </StepProgressCircle>
            <StepProgressLabel incomplete={i > currentStepIndex}>
              {step}
            </StepProgressLabel>
          </StepProgressStep>
          {i < steps.length - 1 && <StepProgressLine />}
        </React.Fragment>
      ))}
    </StepProgressRow>
  )
}

export const StepPanel = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 70px;
  min-height: 300px;
  padding: 50px 70px;
  > * {
    flex: 1;
  }
`

const StepActionsRow = styled.div`
  display: flex;
  padding: 20px;
  background-color: ${Colors.LIGHT_GRAY5};
  justify-content: space-between;
  border-radius: 0 0 3px 3px;
`

export const StepActions: React.FC<{
  left?: React.ReactElement
  right?: React.ReactElement
}> = ({ left, right }) => (
  <StepActionsRow>
    {left || <div />}
    {right || <div />}
  </StepActionsRow>
)
