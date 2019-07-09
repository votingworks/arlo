import React from 'react'
import { render, fireEvent } from '@testing-library/react'
import Header from './Header'

it('renders correctly', () => {
  const { container, getByText } = render(<Header />)
  expect(container).toMatchSnapshot()
  fireEvent.click(getByText('Clear & Restart'))
  expect(container).toMatchSnapshot()
})
