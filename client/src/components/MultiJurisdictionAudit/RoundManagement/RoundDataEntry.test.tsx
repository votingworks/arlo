import React from 'react'
import { render } from '@testing-library/react'
import RoundDataEntry from './RoundDataEntry'
import { roundMocks } from '../_mocks'

describe('offline round data entry', () => {
  it('renders', () => {
    // TODO code offline data entry
    const { container } = render(
      <RoundDataEntry round={roundMocks.singleIncomplete[0]} />
    )
    expect(container).toMatchSnapshot()
  })
})
