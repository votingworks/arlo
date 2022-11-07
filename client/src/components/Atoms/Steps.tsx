import React from 'react'
import styled from 'styled-components'
import { Card, Colors, H5, Icon } from '@blueprintjs/core'

/**
 * A set of components to display a multi-step process. Consists of a card
 * containing:
 *  - a step progress list (top)
 *  - a step content panel (middle)
 *  - a step actions bar (bottom)
 *
 * These components are solely graphical - the parent must manage relevant state
 * (step completion, current step, navigation, disabling, etc.)
 *
 * Example usage:
 *
 *  <Steps>
 *    <StepList>
 *      <StepListItem stepNumber={1} state="complete">Log In</StepListItem>
 *      <StepListItem stepNumber={2} state="current" >Prepare</StepListItem>
 *      <StepListItem stepNumber={3} state="incomplete">Audit Ballots</StepListItem>
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

type StepState = 'incomplete' | 'current' | 'complete'

export const StepListItemCircle = styled.div<{
  state: StepState
}>`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 30px;
  width: 30px;
  border-radius: 50%;
  opacity: ${props => (props.state === 'complete' ? 0.7 : 1)};
  background-color: ${props =>
    props.state === 'incomplete' ? Colors.GRAY4 : Colors.BLUE3};
  margin-right: 10px;
  color: ${Colors.WHITE};
  font-weight: 500;
`

const StepListItemLabel = styled(({ state: _, ...props }) => (
  <H5 {...props} />
))<{ state: StepState }>`
  color: ${props =>
    props.state === 'current' ? Colors.DARK_GRAY1 : Colors.GRAY3};
  margin: 0;
`

interface IStepListItemProps {
  state: StepState
  stepNumber: number
}

export const StepListItem: React.FC<IStepListItemProps> = ({
  state,
  stepNumber,
  children,
}) => {
  return (
    <StepListItemContainer>
      <StepListItemCircle state={state}>
        {state === 'complete' ? <Icon icon="tick" /> : stepNumber}
      </StepListItemCircle>
      <StepListItemLabel
        aria-current={state === 'current' ? 'step' : undefined}
        state={state}
      >
        {children}
      </StepListItemLabel>
    </StepListItemContainer>
  )
}

const StepListConnector = styled.div`
  flex-grow: 1;
  height: 1px;
  background: ${Colors.GRAY5};
  margin: 0 10px;
`

export const StepList: React.FC = ({ children }) => {
  const stepListItems = React.Children.toArray(children)
  return (
    <StepListContainer>
      {stepListItems.map((stepListItem, index) => (
        // eslint-disable-next-line react/no-array-index-key
        <React.Fragment key={`step-container-${index}`}>
          {stepListItem}
          {index < stepListItems.length - 1 && <StepListConnector />}
        </React.Fragment>
      ))}
    </StepListContainer>
  )
}

export const StepPanel = styled.div<{ noPadding?: boolean }>`
  display: flex;
  justify-content: center;
  gap: 20px;
  height: 400px;
  padding: ${props => (props.noPadding ? '0' : '20px')};
  overflow-y: auto;
`

export const StepPanelColumn = styled.div`
  border-radius: 5px;
  background-color: ${Colors.LIGHT_GRAY5};
  padding: 30px;
  flex: 1;
  display: flex;
  flex-direction: column;
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

// Utility function to compute step state for the most common step list pattern:
// - a single current step
// - all previous steps are complete
// - all subsequent steps are incomplete
export const stepState = (
  stepNumber: number,
  currentStepNumber: number
): StepState =>
  stepNumber < currentStepNumber
    ? 'complete'
    : stepNumber === currentStepNumber
    ? 'current'
    : 'incomplete'
