import React from 'react'
import { render } from '@testing-library/react'
import MemberForm from './MemberForm'

describe('MemberForm', () => {
  it('renders correctly', () => {
    const { container } = render(
      <MemberForm
        setDummy={jest.fn()}
        boardName="board name"
        jurisdictionName="jurisdiction name"
      />
    )
    expect(container).toMatchSnapshot()
  })
})
