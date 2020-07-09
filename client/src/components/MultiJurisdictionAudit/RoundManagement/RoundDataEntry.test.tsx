import React from 'react'
import { render } from '@testing-library/react'
import RoundDataEntry from './RoundDataEntry'

describe('offline round data entry', () => {
  it('renders', () => {
    // TODO code offline data entry
    const { container } = render(<RoundDataEntry />)
    expect(container).toMatchSnapshot()
  })
})
