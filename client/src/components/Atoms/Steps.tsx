import React from 'react'
import styled from 'styled-components'
import { Card, Colors, Icon } from '@blueprintjs/core'
import { assert } from '../utilities'

/**
 * A set of components to display a multi-step process. Consists of a card
 * containing:
 *  - a step progress list (top)
 *  - a step content panel (middle)
 *  - a step actions bar (bottom)
 *
 * These components are mostly graphical - the parent must manage relevant state
 * (current step, navigation, disabling, etc.)
 *
 * Example usage:
 *
 *  <Steps>
 *    <StepList currentStepId="prepare">
 *      <StepListItem id="logIn">Log In</StepListItem>
 *      <StepListItem id="prepare">Prepare</StepListItem>
 *      <StepListItem id="audit">Audit Ballots</StepListItem>
 *    </StepList>
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

const StepListContainer = styled.ol`
  background-color: ${Colors.LIGHT_GRAY5};
  display: flex;
  align-items: center;
  padding: 25px;
  margin: 0;
  border-radius: 3px 3px 0 0;
`

const StepListItemContainer = styled.li`
  display: flex;
  align-items: center;
`

const StepListItemCircle = styled.div<{ isIncomplete: boolean }>`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 30px;
  width: 30px;
  border-radius: 50%;
  background-color: ${props =>
    props.isIncomplete ? Colors.GRAY4 : Colors.BLUE3};
  margin-right: 10px;
  color: ${Colors.WHITE};
  font-weight: 500;
`

const StepListItemLabel = styled.div<{ isIncomplete: boolean }>`
  color: ${props => (props.isIncomplete ? Colors.GRAY3 : 'inherit')};
  font-weight: 700;
`

const StepListItemLine = styled.div`
  flex-grow: 1;
  height: 1px;
  background: ${Colors.GRAY5};
  margin: 0 10px;
`

export const StepList: React.FC<{ currentStepId: string }> = ({
  currentStepId,
  children,
}) => {
  const steps = React.Children.toArray(children)
  const currentStepIndex = steps
    .map(step => {
      assert(React.isValidElement(step))
      return step.props.id
    })
    .indexOf(currentStepId)
  return (
    <StepListContainer>
      {steps.map((step, index) => {
        assert(React.isValidElement(step))
        const isCurrent = index === currentStepIndex
        const isComplete = index < currentStepIndex
        const isIncomplete = index > currentStepIndex
        return (
          <React.Fragment key={step.props.id}>
            <StepListItemContainer aria-current={isCurrent}>
              <StepListItemCircle isIncomplete={isIncomplete}>
                {isComplete ? <Icon icon="tick" /> : index + 1}
              </StepListItemCircle>
              <StepListItemLabel isIncomplete={isIncomplete}>
                {step}
              </StepListItemLabel>
            </StepListItemContainer>
            {index < steps.length - 1 && <StepListItemLine />}
          </React.Fragment>
        )
      })}
    </StepListContainer>
  )
}

// eslint-disable-next-line react/no-unused-prop-types
export const StepListItem: React.FC<{ id: string }> = ({ children }) => (
  <React.Fragment>{children}</React.Fragment>
)

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
