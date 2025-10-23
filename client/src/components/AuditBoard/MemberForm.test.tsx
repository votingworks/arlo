import { describe, expect, it, vi } from 'vitest'
import React from 'react'
import { render, fireEvent, waitFor } from '@testing-library/react'
import MemberForm from './MemberForm'

describe('MemberForm', () => {
  it('renders correctly', () => {
    const { container } = render(
      <MemberForm
        boardName="board name"
        jurisdictionName="jurisdiction name"
        submitMembers={vi.fn()}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('handles inputs', async () => {
    const submitMembersMock = vi.fn()
    const { queryAllByLabelText, queryAllByText, getByText } = render(
      <MemberForm
        boardName="board name"
        jurisdictionName="jurisdiction name"
        submitMembers={submitMembersMock}
      />
    )

    const names = queryAllByLabelText('Full Name') as HTMLInputElement[]
    const parties = queryAllByText('Democrat') as HTMLInputElement[]
    expect(names.length).toBe(2)
    expect(parties.length).toBe(2)
    names.forEach(nameInput => {
      fireEvent.change(nameInput, { target: { value: 'my name' } })
      expect(nameInput.value)
    })
    parties.forEach(partyInput => {
      fireEvent.click(partyInput, { bubbles: true })
    })

    const nextButton = getByText('Next')
    fireEvent.click(nextButton, { bubbles: true })
    await waitFor(() => {
      expect(submitMembersMock).toBeCalledTimes(1)
    })
  })
})
