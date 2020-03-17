import React from 'react'
import { render, fireEvent, wait } from '@testing-library/react'
import { statusStates } from '../../_mocks'
import Participants from './index'

describe('Audit Setup > Contests', () => {
  it('renders empty state correctly', () => {
    const { container } = render(
      <Participants audit={statusStates[0]} nextStage={jest.fn()} />
    )
    expect(container).toMatchSnapshot()
  })

  it('selects a state and submits it', async () => {
    const nextStageMock = jest.fn()
    const { getByText, getByTestId } = render(
      <Participants audit={statusStates[0]} nextStage={nextStageMock} />
    )

    fireEvent.change(getByTestId('state-field'), {
      target: { value: 'Alabama' },
    })
    // await wait(() => expect(queryByText('Your state is: Alabama')).toBeTruthy())
    fireEvent.click(getByText('Submit & Next'), { bubbles: true })
    await wait(() => expect(nextStageMock).toHaveBeenCalledTimes(1))
  })
})
