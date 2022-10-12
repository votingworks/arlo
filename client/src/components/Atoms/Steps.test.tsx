import React from 'react'
import { render, screen } from '@testing-library/react'
import { Button, Colors } from '@blueprintjs/core'
import { Steps, StepList, StepListItem, StepPanel, StepActions } from './Steps'

describe('Steps', () => {
  it('renders a step list, panel, and actions', () => {
    render(
      <Steps>
        <StepList>
          <StepListItem>Log In</StepListItem>
          <StepListItem current>Prepare</StepListItem>
          <StepListItem>Audit Ballots</StepListItem>
        </StepList>
        <StepPanel>Prepare your ballots</StepPanel>
        <StepActions
          left={<Button>Back</Button>}
          right={<Button>Next</Button>}
        />
      </Steps>
    )

    const logInHeader = screen.getByRole('heading', {
      name: 'Log In',
      current: undefined,
    })
    expect(logInHeader).toHaveStyle({ color: Colors.GRAY3 })
    const logInCircle = logInHeader.previousElementSibling!
    expect(logInCircle.querySelector("[data-icon='tick']")).toBeInTheDocument()
    expect(logInCircle).toHaveStyle({ backgroundColor: Colors.BLUE3 })
    expect(logInCircle).toHaveStyle({ opacity: 0.7 })

    const prepareHeader = screen.getByRole('heading', {
      name: 'Prepare',
      current: 'step',
    })
    expect(prepareHeader).toHaveStyle({ color: Colors.DARK_GRAY1 })
    const prepareCircle = prepareHeader.previousElementSibling!
    expect(prepareCircle).toHaveTextContent('2')
    expect(prepareCircle).toHaveStyle({ backgroundColor: Colors.BLUE3 })

    const auditHeader = screen.getByRole('heading', {
      name: 'Audit Ballots',
      current: undefined,
    })
    expect(auditHeader).toHaveStyle({ color: Colors.GRAY3 })
    const auditCircle = auditHeader.previousElementSibling!
    expect(auditCircle).toHaveTextContent('3')
    expect(auditCircle).toHaveStyle({ backgroundColor: Colors.GRAY4 })

    screen.getByText('Prepare your ballots')

    screen.getByRole('button', { name: 'Back' })
    screen.getByRole('button', { name: 'Next' })
  })
})
