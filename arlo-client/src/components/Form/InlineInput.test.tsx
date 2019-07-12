import React from 'react'
import { render } from '@testing-library/react'
import InlineInput from './InlineInput'

it('renders corretly', () => {
  const { container } = render(<InlineInput />)
  expect(container).toMatchSnapshot()
})
