import React from 'react'
import { render, fireEvent } from '@testing-library/react'
import Header from './Header'

it('renders correctly at /home', () => {
  const { container, queryByText } = render(<Header match={null} isHome />)
  expect(container).toMatchSnapshot()
  expect(queryByText('Clear & Restart')).toBeFalsy()
  expect(container).toMatchSnapshot()
})

it('renders correctly at /election', () => {
  const { container, getByText } = render(<Header match={null} />)
  expect(container).toMatchSnapshot()
  fireEvent.click(getByText('Clear & Restart'))
  expect(container).toMatchSnapshot()
})
