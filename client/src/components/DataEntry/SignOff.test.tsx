import React from 'react'
import { render, fireEvent, waitFor, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SignOff from './SignOff'
import { dummyBoards } from './_mocks'

describe('Sign Off', () => {
  it('renders correctly', () => {
    const { container } = render(
      <SignOff auditBoard={dummyBoards()[0]} submitSignoff={jest.fn()} />
    )
    expect(container).toMatchSnapshot()
  })

  it('handles inputs', async () => {
    const submitSignoffMock = jest.fn()
    const { container, queryAllByLabelText, getByText } = render(
      <SignOff
        auditBoard={dummyBoards()[0]}
        submitSignoff={submitSignoffMock}
      />
    )

    const nameInputs = screen.getAllByLabelText('Full Name')
    const names = queryAllByLabelText('Full Name') as HTMLInputElement[]
    expect(names.length).toBe(2)
    expect(nameInputs).toHaveLength(2)

    userEvent.type(names[0], `John Doe`)
    userEvent.type(names[1], `Jane Doe`)

    const nextButton = getByText('Sign Off')
    fireEvent.click(nextButton, { bubbles: true })
    await waitFor(() => {
      expect(submitSignoffMock).toBeCalledTimes(1)
    })
    expect(container).toMatchSnapshot()
  })
})
