import React from 'react'
import styled from 'styled-components'
import { Card, Colors, H5, Icon } from '@blueprintjs/core'
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
 *    <StepList>
 *      <StepListItem>Log In</StepListItem>
 *      <StepListItem current>Prepare</StepListItem>
 *      <StepListItem>Audit Ballots</StepListItem>
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

const StepListItemCircle = styled.div<{
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

// eslint-disable-next-line no-unused-vars, @typescript-eslint/no-unused-vars
const StepListItemLabel = styled(({ current, ...props }) => <H5 {...props} />)<{
  current: boolean
}>`
  color: ${props => (props.current ? Colors.DARK_GRAY5 : Colors.GRAY3)};
  margin: 0;
`

interface IStepListItemProps {
  state: StepState
  stepNumber?: number
}

export const StepListItem: React.FC<IStepListItemProps> = ({
  state,
  stepNumber,
  children,
}) => {
  return (
    <StepListItemContainer
      aria-current={state === 'current' ? 'step' : undefined}
    >
      <StepListItemCircle state={state}>
        {state === 'complete' ? <Icon icon="tick" /> : stepNumber}
      </StepListItemCircle>
      <StepListItemLabel current={state === 'current'}>
        {children}
      </StepListItemLabel>
    </StepListItemContainer>
  )
}

const StepListItemLine = styled.div`
  flex-grow: 1;
  height: 1px;
  background: ${Colors.GRAY5};
  margin: 0 10px;
`

export const StepList: React.FC = ({ children }) => {
  const stepListItems = React.Children.toArray(children)
  return (
    <StepListContainer>
      {stepListItems.map((stepItem, index) => {
        assert(React.isValidElement(stepItem))
        return (
          <React.Fragment key={stepItem.key || index}>
            {React.cloneElement(stepItem, {
              stepNumber: stepItem.props.stepNumber ?? index + 1,
            })}
            {index < stepListItems.length - 1 && <StepListItemLine />}
          </React.Fragment>
        )
      })}
    </StepListContainer>
  )
}

export const StepPanel = styled.div`
  display: flex;
  align-items: stretch;
  justify-content: center;
  gap: 20px;
  min-height: 400px;
  padding: 20px;
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
